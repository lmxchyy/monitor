from __future__ import annotations

import datetime as dt
import json
from abc import ABC, abstractmethod

from sources.types import HiringSnapshot


class HiringSource(ABC):
    channel: str

    @abstractmethod
    def fetch(self, company: dict, run_date: dt.date) -> HiringSnapshot | None:  # pragma: no cover
        raise NotImplementedError


def snapshot_to_row(s: HiringSnapshot) -> dict:
    return {
        "company_id": s.company_id,
        "snapshot_date": s.snapshot_date,
        "channel": s.channel,
        "open_jobs_count": int(s.open_jobs_count),
        "categories": "|".join([c for c in s.categories if c]),
        "keywords": "|".join([k for k in s.keywords if k]),
        "source_url": s.source_url,
        "raw_payload": s.raw_payload,
        "confidence": float(s.confidence),
    }


def json_dumps_compact(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
