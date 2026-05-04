#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$ROOT_DIR/data/companies.csv" ]]; then
  echo "Missing $ROOT_DIR/data/companies.csv"
  echo "Please put your companies CSV there (must include column: name)."
  exit 1
fi

echo "[1/6] Starting MySQL (Docker Compose)"
docker compose -f "$ROOT_DIR/docker/compose.yml" up -d

echo "[2/6] Waiting for MySQL to accept connections"
until docker exec monitor-mysql mysql -umonitor -pmonitor -e "SELECT 1" >/dev/null 2>&1; do
  sleep 2
done

echo "[3/6] Creating Python venv (if missing)"
if [[ ! -d "$ROOT_DIR/.venv" ]]; then
  python -m venv "$ROOT_DIR/.venv"
fi

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv/Scripts/activate"

echo "[4/6] Installing Python requirements"
pip install -r "$ROOT_DIR/etl/requirements.txt"

export MONITOR_DB_HOST="127.0.0.1"
export MONITOR_DB_PORT="3306"
export MONITOR_DB_USER="monitor"
export MONITOR_DB_PASSWORD="monitor"
export MONITOR_DB_NAME="monitor"

TODAY="$(python -c "import datetime as d; print(d.date.today().isoformat())")"

echo "[5/6] Running ETL: import companies, hiring"
python "$ROOT_DIR/etl/import_companies.py" --csv "$ROOT_DIR/data/companies.csv"
python "$ROOT_DIR/etl/run_hiring_daily.py" --date "$TODAY"

echo "[6/6] Running ETL: funding placeholders, daily metrics"
python "$ROOT_DIR/etl/run_funding_daily.py" --date "$TODAY"
python "$ROOT_DIR/etl/daily_job.py" --date "$TODAY"

echo "Done. Date=$TODAY"
