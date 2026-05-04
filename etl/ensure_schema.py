from __future__ import annotations

from sqlalchemy import create_engine, text

from lib.db import load_db_config


def main() -> None:
    cfg = load_db_config()
    engine = create_engine(
        f"mysql+pymysql://{cfg.user}:{cfg.password}@{cfg.host}:{cfg.port}/{cfg.name}?charset=utf8mb4"
    )

    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :schema_name
                  AND TABLE_NAME = 'companies'
                """
            ),
            {"schema_name": cfg.name},
        ).scalars()
        columns = set(rows)

        if "industry" not in columns:
            conn.execute(
                text(
                    """
                    ALTER TABLE companies
                    ADD COLUMN industry VARCHAR(64) NOT NULL DEFAULT '综合/其他'
                    AFTER aliases
                    """
                )
            )
            print("Added companies.industry")
        else:
            print("Schema already up to date")


if __name__ == "__main__":
    main()
