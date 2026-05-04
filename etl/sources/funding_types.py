from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class FundingEvent:
    company_id: int
    event_date: dt.date | None
    round: str | None
    amount: str | None
    currency: str | None
    investors: str | None
    source_type: str
    source_url: str | None
    raw_text: str | None
    fingerprint: str
    confidence: float
