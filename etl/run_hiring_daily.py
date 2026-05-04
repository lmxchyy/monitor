import argparse
import datetime as dt

from lib.store import get_all_companies, upsert_hiring_snapshots
from sources.base import snapshot_to_row
from sources.hiring_company_website import CompanyWebsiteSource
from sources.hiring_thirdparty_placeholders import (
    BossZhipinSource,
    ZhilianSource,
    _Placeholder51JobSource,
)


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = parse_date(args.date)

    sources = [
        CompanyWebsiteSource(),
        BossZhipinSource(),
        ZhilianSource(),
        _Placeholder51JobSource(),
    ]

    companies = get_all_companies()

    rows: list[dict] = []
    for c in companies:
        for s in sources:
            snap = s.fetch(c, run_date)
            if snap is None:
                continue
            rows.append(snapshot_to_row(snap))

    upsert_hiring_snapshots(rows)
    print(f"Stored {len(rows)} hiring snapshots for {run_date}")


if __name__ == "__main__":
    main()
