from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

logger = logging.getLogger("core_orchestrator.server")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent.parent
SCROLLSTREAM_LEDGER = BASE_DIR / "data" / "scrollstream" / "scrollstream_ledger.ndjson"


def _load_scrollstream_events() -> list[dict]:
    if not SCROLLSTREAM_LEDGER.exists():
        return []

    events: list[dict] = []
    with SCROLLSTREAM_LEDGER.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping malformed scrollstream line", extra={"line": line})
    return events


class RequestHandler(BaseHTTPRequestHandler):
    """Serve a minimal health endpoint for smoke tests."""

    server_version = "CoreOrchestratorHTTP/1.0"

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        """Respond to GET requests with a JSON health payload."""

        path = self.path.rstrip("/")

        if path == "/health":
            payload = {"status": "ok"}
            body = json.dumps(payload).encode("utf-8")
            self._send_response(200, body)
            logger.info("Responded to /health request")
        elif path == "/scrollstream/rehearsal":
            payload = {
                "capsule": "capsule.rehearsal.scrollstream.v1",
                "ledger": "scrollstream_ledger",
                "events": _load_scrollstream_events(),
            }
            body = json.dumps(payload).encode("utf-8")
            self._send_response(200, body)
            logger.info("Served rehearsal scrollstream payload with %s events", len(payload["events"]))
        else:
            self._send_response(404, b"{}")
            logger.warning("Unhandled path requested: %s", self.path)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        """Silence the default stdout logging to keep CI logs tidy."""

        logger.debug("Request: " + format, *args)

    def _send_response(self, status_code: int, body: bytes) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer((host, port), RequestHandler)
    logger.info("Starting Core Orchestrator HTTP server on %s:%s", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down HTTP server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
