from __future__ import annotations

import datetime as dt

import feedparser

from lib.utils import (
    company_search_variants,
    extract_event_date,
    funding_confidence,
    is_funding_related_text,
    parse_funding_details,
    stable_fingerprint,
)
from sources.base import json_dumps_compact
from sources.funding_types import FundingEvent


def fetch_rss_events(
    feed_name: str,
    feed_url: str,
    companies: list[dict],
    source_cfg: dict | None = None,
) -> list[FundingEvent]:
    source_cfg = source_cfg or {}
    parsed = feedparser.parse(feed_url)

    company_keywords = []
    for c in companies:
        company_keywords.append((c["id"], company_search_variants(c["name"], c.get("aliases"))))

    events: list[FundingEvent] = []

    for entry in parsed.entries[:200]:
        title = getattr(entry, 'title', '') or ''
        summary = getattr(entry, 'summary', '') or ''
        link = getattr(entry, 'link', None)
        published = getattr(entry, 'published', None)
        full_text = title + ' ' + summary

        # 获取默认发布日期
        pub_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            pp = entry.published_parsed
            pub_date = dt.date(pp.tm_year, pp.tm_mon, pp.tm_mday)
        elif published:
            try:
                pub_date = dt.date.fromisoformat(str(published)[:10])
            except Exception:
                pub_date = None

        # 尝试从文本中提取实际发生日期，提取不到则用发布日期
        event_date = extract_event_date(full_text, default_date=pub_date)

        details = parse_funding_details(full_text)
        if not is_funding_related_text(full_text, details):
            continue

        raw = {
            'feed': feed_name,
            'title': title,
            'published': published,
            'pub_date_fallback': str(pub_date),
            'summary': summary,
            'parsed_details': details,
        }

        matched_company_id = None
        for cid, keywords in company_keywords:
            if any(kw in full_text for kw in keywords if len(kw) >= 2):
                matched_company_id = cid
                break

        if not matched_company_id:
            continue

        fp = stable_fingerprint(['funding', 'rss', feed_name, str(link or title)])
        events.append(
            FundingEvent(
                company_id=matched_company_id,
                event_date=event_date,
                round=details['round'],
                amount=details['amount'],
                currency=details['currency'],
                investors=details['investors'],
                source_type=source_cfg.get("source_type", "rss_candidate"),
                source_url=link,
                raw_text=json_dumps_compact(raw),
                fingerprint=fp,
                confidence=funding_confidence(
                    full_text,
                    details,
                    base=float(source_cfg.get("confidence", 0.300)),
                    source_bonus=float(source_cfg.get("source_bonus", 0.0)),
                ),
            )
        )

    return events
