from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class HiringSnapshot:
    company_id: int
    snapshot_date: dt.date
    channel: str
    open_jobs_count: int
    categories: list[str]
    keywords: list[str]
    source_url: str | None
    raw_payload: str | None
    confidence: float
