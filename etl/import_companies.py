import argparse
import csv

from sqlalchemy import create_engine, text

from lib.db import load_db_config
from lib.utils import guess_industry, normalize_company_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    with open(args.csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "name" not in reader.fieldnames:
            raise SystemExit("CSV must include column: name")
        raw_rows = list(reader)

    rows_by_normalized_name: dict[str, dict] = {}
    for raw in raw_rows:
        name = (raw.get("name") or "").strip()
        if not name:
            continue

        normalized_name = normalize_company_name(name)
        if normalized_name in rows_by_normalized_name:
            continue

        credit_code = (raw.get("credit_code") or "").strip() or None
        aliases = (raw.get("aliases") or "").strip() or None
        rows_by_normalized_name[normalized_name] = {
            "name": name,
            "normalized_name": normalized_name,
            "credit_code": credit_code,
            "aliases": aliases,
            "industry": guess_industry(name),
        }

    rows = list(rows_by_normalized_name.values())
    if not rows:
        raise SystemExit("CSV must include column: name")

    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    update_by_credit_code_sql = text(
        """
        UPDATE companies
        SET name = :name,
            normalized_name = :normalized_name,
            aliases = :aliases,
            industry = :industry
        WHERE credit_code <=> :credit_code
        """
    )

    update_by_normalized_name_sql = text(
        """
        UPDATE companies
        SET name = :name,
            aliases = COALESCE(:aliases, aliases),
            industry = :industry
        WHERE normalized_name = :normalized_name
        """
    )

    insert_sql = text(
        """
        INSERT INTO companies (name, normalized_name, credit_code, aliases, industry, city)
        VALUES (:name, :normalized_name, :credit_code, :aliases, :industry, '北京')
        """
    )

    inserted = 0
    updated = 0
    with engine.begin() as conn:
        for row in rows:
            matched = 0
            if row["credit_code"]:
                result = conn.execute(update_by_credit_code_sql, row)
                matched = result.rowcount
            if matched == 0:
                result = conn.execute(update_by_normalized_name_sql, row)
                matched = result.rowcount
            if matched == 0:
                conn.execute(insert_sql, row)
                inserted += 1
            else:
                updated += 1

    print(f"Inserted {inserted}, updated {updated}, total input {len(rows)} companies")


if __name__ == "__main__":
    main()
