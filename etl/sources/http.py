from __future__ import annotations

import json
import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass(frozen=True)
class FetchResult:
    final_url: str
    status_code: int
    text: str
    api_requests: tuple[str, ...] = ()


_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}


def fetch_html(url: str, timeout_s: int = 20, headers: dict | None = None) -> FetchResult:
    request_headers = _DEFAULT_HEADERS.copy()
    if headers:
        request_headers.update(headers)

    resp = requests.get(url, headers=request_headers, timeout=timeout_s)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or resp.encoding
    return FetchResult(final_url=str(resp.url), status_code=resp.status_code, text=resp.text)


def to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def fetch_html_dynamic(
    url: str,
    wait_selector: str | None = None,
    timeout_ms: int = 30000,
    network_idle: bool = True,
    capture_api: bool = False,
    stealth: bool = False,
) -> FetchResult:
    from playwright.sync_api import sync_playwright

    api_requests: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=_DEFAULT_HEADERS["User-Agent"],
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": _DEFAULT_HEADERS["Accept-Language"],
                "Referer": _DEFAULT_HEADERS["Referer"],
            },
        )
        if stealth:
            context.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """
            )
        page = context.new_page()
        if capture_api:
            page.on("request", lambda request: _record_api_request(request, api_requests))
        try:
            wait_until = "networkidle" if network_idle else "domcontentloaded"
            page.goto(url, timeout=timeout_ms, wait_until=wait_until)
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=10000)
            else:
                page.wait_for_timeout(3000)  # 保底等3秒渲染
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            
            content = page.content()
            final_url = page.url
            return FetchResult(
                final_url=final_url,
                status_code=200,
                text=content,
                api_requests=tuple(api_requests),
            )
        finally:
            browser.close()


def _record_api_request(request, out: list[str]) -> None:
    if request.resource_type not in {"fetch", "xhr"}:
        return
    if request.url in out:
        return
    out.append(request.url)


def fetch_html_auto(
    url: str,
    fetcher: str = "auto",
    wait_selector: str | None = None,
    timeout_s: int = 20,
    timeout_ms: int = 30000,
    capture_api: bool = False,
) -> FetchResult:
    fetcher = (fetcher or "auto").lower()
    if fetcher in {"get", "http", "requests"}:
        return fetch_html(url, timeout_s=timeout_s)
    if fetcher in {"dynamic", "fetch", "playwright"}:
        return fetch_html_dynamic(
            url,
            wait_selector=wait_selector,
            timeout_ms=timeout_ms,
            capture_api=capture_api,
        )
    if fetcher in {"stealth", "stealthy", "stealthy-fetch"}:
        return fetch_html_dynamic(
            url,
            wait_selector=wait_selector,
            timeout_ms=timeout_ms,
            capture_api=capture_api,
            stealth=True,
        )

    try:
        fr = fetch_html(url, timeout_s=timeout_s)
        text_hint = fr.text[:2000].lower()
        if _looks_like_dynamic_page(fr.text, text_hint):
            raise ValueError("page looks dynamic")
        return fr
    except Exception:
        return fetch_html_dynamic(
            url,
            wait_selector=wait_selector,
            timeout_ms=timeout_ms,
            capture_api=capture_api,
            stealth=("itjuzi" in url.lower()),
        )


def _looks_like_dynamic_page(html: str, text_hint: str) -> bool:
    stripped_text = to_soup(html).get_text(" ", strip=True)
    if len(stripped_text) < 100:
        return True
    dynamic_markers = ["loading", "__next", "window.__initial_state__", "root"]
    return any(marker in text_hint for marker in dynamic_markers)


def fetch_result_debug_json(fr: FetchResult) -> str:
    return json.dumps(
        {
            "final_url": fr.final_url,
            "status_code": fr.status_code,
            "api_requests": list(fr.api_requests),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def parse_int_loose(s: str) -> int | None:
    if s is None:
        return None
    m = re.search(r"(\d+)", str(s).replace(",", ""))
    if not m:
        return None
    return int(m.group(1))
