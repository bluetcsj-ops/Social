from __future__ import annotations

import argparse
import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
ADMIN_DIR = ROOT / "admin"
if str(ADMIN_DIR) not in sys.path:
    sys.path.insert(0, str(ADMIN_DIR))


class GrowthDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/admin/growth-dashboard.html")
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/refresh-cloudflare":
            self.send_error(404, "Not found")
            return
        self.refresh_cloudflare()

    def do_OPTIONS(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/refresh-cloudflare":
            self.send_error(404, "Not found")
            return
        self.send_response(204)
        self.end_headers()

    def refresh_cloudflare(self) -> None:
        try:
            import sync_cloudflare

            payload = sync_cloudflare.fetch_cloudflare_growth_data()
            sync_cloudflare.write_growth_data(payload)
            self.send_json(200, {"ok": True, "data": payload})
        except Exception as exc:
            self.send_json(500, {"ok": False, "error": str(exc)})

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        requested_path = unquote(urlparse(self.path).path)
        if requested_path.endswith("growth-data.js"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local growth dashboard refresh server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), GrowthDashboardHandler)
    print(f"Growth dashboard: http://{args.host}:{args.port}/admin/growth-dashboard.html")
    print("Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
