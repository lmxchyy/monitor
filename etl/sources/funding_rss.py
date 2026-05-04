from __future__ import annotations

import datetime as dt

import feedparser

from lib.utils import stable_fingerprint, parse_funding_details, extract_event_date
from sources.base import json_dumps_compact
from sources.funding_types import FundingEvent


def fetch_rss_events(feed_name: str, feed_url: str, companies: list[dict]) -> list[FundingEvent]:
    parsed = feedparser.parse(feed_url)

    company_keywords = []
    for c in companies:
        name = c['name']
        keywords = [name, c['normalized_name']]
        for kw in ['集团', '有限公司', '股份有限公司', '有限责任公司', '科技', '（北京）', '(北京)']:
            name = name.replace(kw, '')
        if name and name not in keywords:
            keywords.append(name.strip())
        company_keywords.append((c['id'], keywords))

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
                source_type='rss_candidate',
                source_url=link,
                raw_text=json_dumps_compact(raw),
                fingerprint=fp,
                confidence=0.300,
            )
        )

    return events
