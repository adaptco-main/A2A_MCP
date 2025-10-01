from __future__ import annotations

import json
import logging
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
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


def _default_static_root() -> Path:
    """Resolve the static asset root from environment or repo defaults."""

    configured = os.environ.get("PORTAL_STATIC_ROOT")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parent.parent / "public"


def _default_portal_entrypoint(static_root: Path) -> Path:
    """Resolve the entrypoint HTML for the portal experience."""

    configured = os.environ.get("PORTAL_ENTRYPOINT")
    if configured:
        candidate = Path(configured)
        if not candidate.is_absolute():
            candidate = static_root / candidate
        return candidate
    return static_root / "hud" / "capsules" / "avatar" / "index.html"


STATIC_ROOT = _default_static_root().resolve()
PORTAL_ENTRYPOINT = _default_portal_entrypoint(STATIC_ROOT).resolve()

try:
    PORTAL_ENTRYPOINT.relative_to(STATIC_ROOT)
except ValueError:  # pragma: no cover - configuration safeguard
    logger.warning(
        "Portal entrypoint %s is not within the static root %s; falling back to default",
        PORTAL_ENTRYPOINT,
        STATIC_ROOT,
    )
    PORTAL_ENTRYPOINT = (STATIC_ROOT / "hud" / "capsules" / "avatar" / "index.html").resolve()

if not PORTAL_ENTRYPOINT.exists():  # pragma: no cover - startup diagnostics
    logger.warning("Portal entrypoint %s does not exist", PORTAL_ENTRYPOINT)

mimetypes.add_type("application/json", ".json")


def resolve_portal_asset(request_path: str) -> Optional[Path]:
    """Map an HTTP request path to an on-disk portal asset if available."""

    normalized = request_path or "/"
    if normalized == "/":
        candidate = PORTAL_ENTRYPOINT
    else:
        relative = normalized.lstrip("/")
        candidate = (STATIC_ROOT / relative).resolve()
        if candidate.is_dir():
            candidate = (candidate / "index.html").resolve()

    try:
        candidate.relative_to(STATIC_ROOT)
    except ValueError:
        return None

    if candidate.is_file():
        return candidate
    return None


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

        if self._serve_portal_asset(path):
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
        self._send_response(status_code, body, "application/json")

    def _serve_portal_asset(self, path: str) -> bool:
        """Serve static assets backing the portal when available."""

        asset_path = resolve_portal_asset(path)
        if asset_path is None:
            return False

        try:
            body = asset_path.read_bytes()
        except OSError as exc:  # pragma: no cover - defensive IO guard
            logger.error("Failed to read portal asset %s: %s", asset_path, exc)
            return False

        content_type = mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream"
        self._send_response(200, body, content_type)
        try:
            relative = asset_path.relative_to(STATIC_ROOT)
        except ValueError:  # pragma: no cover - should not occur
            relative = asset_path
        logger.info("Served portal asset %s", relative)
        return True

    def _send_response(self, status_code: int, body: bytes, content_type: str) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
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
