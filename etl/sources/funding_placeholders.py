from __future__ import annotations

import datetime as dt
from urllib.parse import quote

from lib.utils import stable_fingerprint
from sources.base import json_dumps_compact
from sources.funding_types import FundingEvent


def placeholder_news_event(company: dict, run_date: dt.date) -> FundingEvent:
    name = company["name"]
    q = quote(f"{name} 融资")
    url = f"https://news.google.com/search?q={q}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"
    fp = stable_fingerprint(["funding", "news", str(company["id"]), run_date.isoformat()])
    raw = {"status": "placeholder", "reason": "no-provider", "query": f"{name} 融资"}
    return FundingEvent(
        company_id=int(company["id"]),
        event_date=None,
        round=None,
        amount=None,
        currency=None,
        investors=None,
        source_type="news_placeholder",
        source_url=url,
        raw_text=json_dumps_compact(raw),
        fingerprint=fp,
        confidence=0.050,
    )


def placeholder_disclosure_event(company: dict, run_date: dt.date) -> FundingEvent:
    name = company["name"]
    q = quote(f"{name} 公告 融资")
    url = f"https://www.baidu.com/s?wd={q}"
    fp = stable_fingerprint(["funding", "disclosure", str(company["id"]), run_date.isoformat()])
    raw = {"status": "placeholder", "reason": "no-provider", "query": f"{name} 公告 融资"}
    return FundingEvent(
        company_id=int(company["id"]),
        event_date=None,
        round=None,
        amount=None,
        currency=None,
        investors=None,
        source_type="disclosure_placeholder",
        source_url=url,
        raw_text=json_dumps_compact(raw),
        fingerprint=fp,
        confidence=0.050,
    )
