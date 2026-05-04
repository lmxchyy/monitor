
import pymysql
import os

from etl.lib.utils import guess_industry

def db_cfg():
    return {
        "host": os.getenv("MONITOR_DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("MONITOR_DB_PORT", "3306")),
        "user": os.getenv("MONITOR_DB_USER", "monitor"),
        "password": os.getenv("MONITOR_DB_PASSWORD", "monitor"),
        "db": os.getenv("MONITOR_DB_NAME", "monitor"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
    }

def main():
    cfg = db_cfg()
    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM companies")
            rows = cur.fetchall()
            for r in rows:
                industry = guess_industry(r['name'])
                cur.execute("UPDATE companies SET industry=%s WHERE id=%s", (industry, r['id']))
        conn.commit()
        print(f"Tagged {len(rows)} companies with industry labels.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
