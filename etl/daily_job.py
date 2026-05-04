import argparse
import datetime as dt

from lib.store import upsert_daily_metrics_placeholders


def parse_date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    run_date = parse_date(args.date)

    # v1: 由于暂无供应商/接口，采集模块先以占位实现打通链路。
    upsert_daily_metrics_placeholders(run_date)

    print(f"Daily job completed for {run_date}")


if __name__ == "__main__":
    main()
