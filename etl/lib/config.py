from __future__ import annotations

from pathlib import Path

import yaml


def load_sources_config() -> dict:
    path = Path(__file__).resolve().parents[1] / "config" / "sources.yml"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
