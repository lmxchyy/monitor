from __future__ import annotations

import datetime as dt

from sqlalchemy import create_engine, text

from lib.db import load_db_config


def get_all_companies() -> list[dict]:
    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    sql = text("SELECT id, name, normalized_name, credit_code, aliases FROM companies")
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return [dict(r) for r in rows]


def upsert_hiring_snapshots(snapshots: list[dict]) -> None:
    if not snapshots:
        return

    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    sql = text(
        """
        INSERT INTO hiring_snapshots (
          company_id, snapshot_date, channel, open_jobs_count,
          categories, keywords, source_url, raw_payload, confidence
        )
        VALUES (
          :company_id, :snapshot_date, :channel, :open_jobs_count,
          :categories, :keywords, :source_url, :raw_payload, :confidence
        )
        ON DUPLICATE KEY UPDATE
          open_jobs_count = VALUES(open_jobs_count),
          categories = VALUES(categories),
          keywords = VALUES(keywords),
          source_url = VALUES(source_url),
          raw_payload = VALUES(raw_payload),
          confidence = VALUES(confidence)
        """
    )

    with engine.begin() as conn:
        for s in snapshots:
            conn.execute(sql, s)


def upsert_funding_events(events: list[dict]) -> None:
    if not events:
        return

    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    sql = text(
        """
        INSERT INTO funding_events (
          company_id, event_date, round, amount, currency, investors,
          source_type, source_url, raw_text, fingerprint, confidence
        )
        VALUES (
          :company_id, :event_date, :round, :amount, :currency, :investors,
          :source_type, :source_url, :raw_text, :fingerprint, :confidence
        )
        ON DUPLICATE KEY UPDATE
          event_date = VALUES(event_date),
          round = VALUES(round),
          amount = VALUES(amount),
          currency = VALUES(currency),
          investors = VALUES(investors),
          source_type = VALUES(source_type),
          source_url = VALUES(source_url),
          raw_text = VALUES(raw_text),
          confidence = VALUES(confidence)
        """
    )

    with engine.begin() as conn:
        for e in events:
            conn.execute(sql, e)


def upsert_daily_metrics_placeholders(run_date: dt.date) -> None:
    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    # 真实的指标计算 SQL
    metrics_sql = text(
        """
        INSERT INTO company_daily_metrics (
          company_id, date,
          open_jobs_total, open_jobs_7d_delta, open_jobs_30d_delta,
          funding_last_90d_count, latest_funding_date
        )
        SELECT
          c.id AS company_id,
          :run_date AS date,
          COALESCE(h.total_jobs, 0) AS open_jobs_total,
          0 AS open_jobs_7d_delta,
          0 AS open_jobs_30d_delta,
          COALESCE(f.funding_count, 0) AS funding_last_90d_count,
          f.latest_date AS latest_funding_date
        FROM companies c
        LEFT JOIN (
            SELECT company_id, SUM(open_jobs_count) as total_jobs
            FROM hiring_snapshots
            WHERE snapshot_date = :run_date
            GROUP BY company_id
        ) h ON c.id = h.company_id
        LEFT JOIN (
            SELECT 
                company_id, 
                COUNT(*) as funding_count,
                MAX(event_date) as latest_date
            FROM funding_events
            WHERE event_date BETWEEN DATE_SUB(:run_date, INTERVAL 90 DAY) AND :run_date
            GROUP BY company_id
        ) f ON c.id = f.company_id
        ON DUPLICATE KEY UPDATE
          open_jobs_total = VALUES(open_jobs_total),
          funding_last_90d_count = VALUES(funding_last_90d_count),
          latest_funding_date = VALUES(latest_funding_date)
        """
    )

    with engine.begin() as conn:
        conn.execute(metrics_sql, {"run_date": run_date})
