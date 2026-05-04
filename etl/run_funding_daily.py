import argparse
import datetime as dt

from lib.config import load_sources_config
from lib.store import get_all_companies, upsert_funding_events
from lib.utils import (
    company_search_variants,
    extract_event_date,
    funding_confidence,
    is_funding_related_text,
    parse_funding_details,
    stable_fingerprint,
)
from sources.funding_rss import fetch_rss_events
from sources.base import json_dumps_compact
from sources.http import fetch_html_auto, fetch_result_debug_json, to_soup
from sources.funding_types import FundingEvent


def _extract_blocks(html: str, selectors: list[str] | None = None) -> list[str]:
    soup = to_soup(html)
    blocks: list[str] = []

    selector_list = selectors or ["tr", ".list-item", "li", "article", "section", "div"]
    for selector in selector_list:
        for node in soup.select(selector):
            txt = node.get_text(" ", strip=True)
            if len(txt) > 20 and txt not in blocks:
                blocks.append(txt)

    if not blocks:
        text = soup.get_text("\n", strip=True)
        for line in text.splitlines():
            txt = " ".join(line.split())
            if len(txt) > 20 and txt not in blocks:
                blocks.append(txt)

    return blocks


def fetch_web_list_events(source_cfg: dict, companies: list[dict], run_date: dt.date) -> list[FundingEvent]:
    name = source_cfg.get("name") or "web"
    url = source_cfg.get("url")
    if not url:
        return []

    events = []
    try:
        fetcher = source_cfg.get("fetcher") or ("stealth" if "itjuzi" in url.lower() else "auto")
        wait_selector = source_cfg.get("wait_selector")
        selectors = source_cfg.get("selectors") or source_cfg.get("block_selectors")
        capture_api = bool(source_cfg.get("capture_api", False))

        print(f"Fetch web list {name} via {fetcher}...")
        fr = fetch_html_auto(
            url,
            fetcher=fetcher,
            wait_selector=wait_selector,
            capture_api=capture_api,
        )
        blocks = _extract_blocks(fr.text, selectors)
        print(
            f"Fetched {name}: blocks={len(blocks)}, api_requests={len(fr.api_requests)}, final_url={fr.final_url}"
        )

        company_keywords = []
        for c in companies:
            company_keywords.append((c["id"], company_search_variants(c["name"], c.get("aliases"))))

        for block in blocks:
            matched_company_id = None
            for cid, keywords in company_keywords:
                if any(kw in block for kw in keywords if len(kw) >= 2):
                    matched_company_id = cid
                    break
            if not matched_company_id:
                continue

            details = parse_funding_details(block)
            if not is_funding_related_text(block, details):
                continue

            fp = stable_fingerprint(["funding", "web", name, block[:100]])
            events.append(
                FundingEvent(
                    company_id=matched_company_id,
                    event_date=extract_event_date(block, default_date=run_date),
                    round=details["round"],
                    amount=details["amount"],
                    currency=details["currency"],
                    investors=details["investors"],
                    source_type=source_cfg.get("source_type", "web_list"),
                    source_url=fr.final_url or url,
                    raw_text=json_dumps_compact(
                        {
                            "source": name,
                            "text": block,
                            "fetch": fetch_result_debug_json(fr),
                        }
                    ),
                    fingerprint=fp,
                    confidence=funding_confidence(
                        block,
                        details,
                        base=float(source_cfg.get("confidence", 0.350)),
                        source_bonus=float(source_cfg.get("source_bonus", 0.0)),
                    ),
                )
            )
    except Exception as e:
        print(f"Failed to fetch web list {name}: {e}")
    return events


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def event_to_row(e) -> dict:
    return {
        "company_id": e.company_id,
        "event_date": e.event_date,
        "round": e.round,
        "amount": e.amount,
        "currency": e.currency,
        "investors": e.investors,
        "source_type": e.source_type,
        "source_url": e.source_url,
        "raw_text": e.raw_text,
        "fingerprint": e.fingerprint,
        "confidence": e.confidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = parse_date(args.date)

    companies = get_all_companies()
    cfg = load_sources_config()

    events = []

    rss_feeds = ((cfg.get("funding") or {}).get("rss_feeds")) or []
    if rss_feeds:
        for f in rss_feeds:
            name = f.get("name") or "rss"
            url = f.get("url")
            if not url:
                continue
            events.extend(fetch_rss_events(name, url, companies, f))

    web_lists = ((cfg.get("funding") or {}).get("disclosure_lists")) or []
    if web_lists:
        for f in web_lists:
            events.extend(fetch_web_list_events(f, companies, run_date))

    rows = [event_to_row(e) for e in events]
    if rows:
        upsert_funding_events(rows)
    print(f"Stored {len(rows)} real funding events for {run_date}")


if __name__ == "__main__":
    main()
