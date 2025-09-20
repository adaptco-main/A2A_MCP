from __future__ import annotations

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlsplit

from .merge_model import MergeModel

logger = logging.getLogger("core_orchestrator.server")
logging.basicConfig(level=logging.INFO)


def _default_model_path() -> Path:
    """Resolve the merge model path from environment or repository defaults."""

    configured = os.environ.get("MERGE_MODEL_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent.parent / "specs" / "branch-merge-model.v1.json"


try:
    MERGE_MODEL = MergeModel.from_file(_default_model_path())
    logger.info("Loaded merge model with version %s", MERGE_MODEL.version)
except (FileNotFoundError, json.JSONDecodeError) as exc:  # pragma: no cover - defensive
    logger.error("Unable to load merge model: %s", exc)
    MERGE_MODEL = MergeModel.empty()


class RequestHandler(BaseHTTPRequestHandler):
    """Serve merge-planning metadata and middleware introspection."""

    server_version = "CoreOrchestratorHTTP/1.1"
    merge_model: MergeModel = MERGE_MODEL

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler API)
        """Respond to GET requests with merge-planning artefacts."""

        path = self._normalized_path()
        if path == "/health":
            self._respond_json(200, {"status": "ok"})
            logger.info("Responded to /health request")
            return

        if path == "/merge/branches":
            payload = {
                "version": self.merge_model.version,
                "updated": self.merge_model.updated,
                "branches": self.merge_model.branches_summary(),
            }
            self._respond_json(200, payload)
            logger.info("Served merge branches metadata")
            return

        if path == "/merge/plan":
            payload = {
                "version": self.merge_model.version,
                "updated": self.merge_model.updated,
                "waves": self.merge_model.plan_summary(),
            }
            self._respond_json(200, payload)
            logger.info("Served merge plan summary")
            return

        if path == "/merge/automation":
            payload = {
                "version": self.merge_model.version,
                "updated": self.merge_model.updated,
                "automation": self.merge_model.automation_summary(),
            }
            self._respond_json(200, payload)
            logger.info("Served automation summary")
            return

        if path == "/middleware/contract":
            payload = {
                "version": self.merge_model.version,
                "updated": self.merge_model.updated,
                "contract": self.merge_model.middleware_summary(),
            }
            self._respond_json(200, payload)
            logger.info("Served middleware contract")
            return

        if path == "/merge/model":
            payload = self.merge_model.to_dict()
            self._respond_json(200, payload)
            logger.info("Served full merge model payload")
            return

        self._respond_json(404, {"error": "not_found", "path": path})
        logger.warning("Unhandled path requested: %s", self.path)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        """Silence the default stdout logging to keep CI logs tidy."""

        logger.debug("Request: " + format, *args)

    def _normalized_path(self) -> str:
        """Normalize request path to support suffix slashes and query strings."""

        raw_path = urlsplit(self.path).path
        normalized = raw_path.rstrip("/")
        return normalized or "/"

    def _respond_json(self, status_code: int, payload: Dict[str, Any]) -> None:
        """Helper to serialize payloads to JSON."""

        body = json.dumps(payload).encode("utf-8")
        self._send_response(status_code, body)

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
