
import pymysql
import os
import json

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
            cur.execute("SELECT id, company_id, event_date, raw_text FROM funding_events WHERE source_type='rss_candidate' ORDER BY id DESC LIMIT 3")
            rows = cur.fetchall()
            for r in rows:
                print(f"ID: {r['id']} | Event Date: {r['event_date']}")
                raw = json.loads(r['raw_text'])
                print(f"Title: {raw.get('title')}")
                # print(f"Parsed Details: {raw.get('parsed_details')}")
                print("-" * 20)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
