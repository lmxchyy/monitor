#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${MONITOR_DB_NAME:-monitor}"
DB_USER="${MONITOR_DB_USER:-monitor}"
DB_PASS="${MONITOR_DB_PASSWORD:-monitor}"
CONTAINER="${MONITOR_DB_CONTAINER:-monitor-mysql}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${MONITOR_OUT_DIR:-$ROOT_DIR/results}"
mkdir -p "$OUT_DIR"
OUT_FILE="$OUT_DIR/results_$(date +%F).txt"

run() {
  local sql="$1"
  docker exec "$CONTAINER" mysql \
    --default-character-set=utf8mb4 \
    -u"$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "$sql"
}

{
  echo "Generated: $(date -Iseconds)"
  echo

  echo "== Companies (top 20) =="
  run "SELECT id,name,aliases FROM companies ORDER BY id LIMIT 20;"

  echo
  echo "== Hiring snapshots by date/channel =="
  run "SELECT snapshot_date, channel, COUNT(*) cnt FROM hiring_snapshots GROUP BY snapshot_date, channel ORDER BY snapshot_date DESC, channel;"

  echo
  echo "== Latest hiring snapshots (10) =="
  run "SELECT h.id, h.snapshot_date, c.name, h.channel, h.open_jobs_count, h.keywords, h.source_url FROM hiring_snapshots h JOIN companies c ON c.id=h.company_id ORDER BY h.id DESC LIMIT 10;"

  echo
  echo "== Funding events by source_type =="
  run "SELECT source_type, COUNT(*) cnt FROM funding_events GROUP BY source_type ORDER BY source_type;"

  echo
  echo "== Latest funding events (10) =="
  run "SELECT f.id, c.name, f.source_type, f.event_date, f.source_url, f.raw_text FROM funding_events f JOIN companies c ON c.id=f.company_id ORDER BY f.id DESC LIMIT 10;"

  echo
  echo "== Daily metrics (latest date, top 20) =="
  run "SELECT m.date, c.name, m.open_jobs_total, m.funding_last_90d_count, m.latest_funding_date FROM company_daily_metrics m JOIN companies c ON c.id=m.company_id ORDER BY m.date DESC, c.id LIMIT 20;"
} > "$OUT_FILE"

echo "$OUT_FILE"

if [[ -d "$ROOT_DIR/.venv" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.venv/Scripts/activate"
  python "$ROOT_DIR/show_results_html.py"
else
  echo "(Skip html) venv not found: $ROOT_DIR/.venv"
fi
