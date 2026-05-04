from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from sources.http import fetch_html


def extract_links(list_url: str, link_selector: str) -> list[str]:
    fr = fetch_html(list_url)
    soup = BeautifulSoup(fr.text, "lxml")

    links: list[str] = []
    for a in soup.select(link_selector):
        href = a.get("href")
        if not href:
            continue
        abs_url = urljoin(fr.final_url, href)
        if abs_url not in links:
            links.append(abs_url)

    return links
