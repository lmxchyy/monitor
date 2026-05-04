from __future__ import annotations

import argparse
import datetime as dt
import json
import mimetypes
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
WEB_DIR = ROOT / "web"

STATE = {
    "running": False,
    "last_started_at": None,
    "last_finished_at": None,
    "last_ok": None,
    "last_message": "not started",
}
STATE_LOCK = threading.Lock()


def today() -> str:
    return dt.date.today().isoformat()


def latest_report_path() -> Path | None:
    reports = sorted(RESULTS_DIR.glob("results_*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    return reports[0] if reports else None


def run_etl(date: str | None = None) -> None:
    run_date = date or today()
    with STATE_LOCK:
        if STATE["running"]:
            return
        STATE.update(
            {
                "running": True,
                "last_started_at": dt.datetime.now().isoformat(timespec="seconds"),
                "last_message": f"running ETL for {run_date}",
            }
        )

    try:
        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "run_etl.ps1"),
            "-Date",
            run_date,
        ]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
        ok = proc.returncode == 0
        message = (proc.stdout if ok else proc.stderr or proc.stdout).strip()
        if len(message) > 4000:
            message = message[-4000:]
        with STATE_LOCK:
            STATE.update(
                {
                    "last_ok": ok,
                    "last_message": message,
                    "last_finished_at": dt.datetime.now().isoformat(timespec="seconds"),
                }
            )
    except Exception as exc:
        with STATE_LOCK:
            STATE.update(
                {
                    "last_ok": False,
                    "last_message": repr(exc),
                    "last_finished_at": dt.datetime.now().isoformat(timespec="seconds"),
                }
            )
    finally:
        with STATE_LOCK:
            STATE["running"] = False


def scheduler(interval_seconds: int) -> None:
    run_etl()
    while True:
        time.sleep(interval_seconds)
        run_etl()


def status_payload() -> dict:
    report = latest_report_path()
    with STATE_LOCK:
        state = dict(STATE)
    state["report"] = str(report) if report else None
    state["report_mtime"] = (
        dt.datetime.fromtimestamp(report.stat().st_mtime).isoformat(timespec="seconds") if report else None
    )
    state["server_time"] = dt.datetime.now().isoformat(timespec="seconds")
    return state


class Handler(BaseHTTPRequestHandler):
    server_version = "MonitorWeb/1.0"

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_static(WEB_DIR / "index.html")
        elif path == "/report":
            self._send_report()
        elif path == "/status":
            self._send_json(status_payload())
        elif path == "/run-now":
            threading.Thread(target=run_etl, daemon=True).start()
            self._send_json({"started": True})
        elif path.startswith("/assets/"):
            self._send_static(WEB_DIR / path.removeprefix("/assets/"))
        else:
            self.send_error(404)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def _send_html(self, body: str, status: int = 200) -> None:
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_static(self, path: Path) -> None:
        try:
            resolved = path.resolve()
            if not str(resolved).startswith(str(WEB_DIR.resolve())):
                self.send_error(403)
                return
            data = resolved.read_bytes()
        except FileNotFoundError:
            self.send_error(404)
            return

        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        if resolved.suffix == ".js":
            content_type = "text/javascript; charset=utf-8"
        elif resolved.suffix in {".html", ".css"}:
            content_type = f"{content_type}; charset=utf-8"

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_report(self) -> None:
        report = latest_report_path()
        if not report:
            self._send_html("<!doctype html><meta charset='utf-8'><p>No report yet.</p>", status=404)
            return
        data = report.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--interval", type=int, default=int(os.getenv("MONITOR_WEB_INTERVAL", "600")))
    args = parser.parse_args()

    threading.Thread(target=scheduler, args=(args.interval,), daemon=True).start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"monitor web listening on http://{args.host}:{args.port}")
    print(f"ETL interval: {args.interval}s")
    server.serve_forever()


if __name__ == "__main__":
    main()
