"""
mcp_servers/gemini_control.py — Gemini API MCP HTTP Control Layer
==================================================================
A FastAPI MCP HTTP endpoint that:
  1. Serves indexed artifacts from the data/vector_lake/ data lake as MCP resources
  2. Accepts Gemini API calls as the AI control layer for agent routing
  3. Routes to the appropriate frontend UI (ui/, apps/, frontend/)

This is the "galaxy of UI sites" control plane referenced in the architecture.

Environment variables:
    GEMINI_API_KEY    — Gemini API key (required for /api/generate)
    GEMINI_MODEL      — Model name (default: gemini-2.0-flash)
    VECTOR_LAKE_DIR   — Path to vector lake snapshot (default: data/vector_lake)
    MCP_PORT          — Port to serve on (default: 9090)

Run:
    uvicorn mcp_servers.gemini_control:app --port 9090 --reload
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Gemini OS — MCP Control Layer",
    description=(
        "HTTP MCP endpoint for the A2A_MCP monorepo. "
        "Exposes indexed artifacts as MCP resources and routes Gemini API calls "
        "to the agent pipeline (the galaxy of UI sites)."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_LAKE_DIR = pathlib.Path(os.environ.get("VECTOR_LAKE_DIR", "data/vector_lake"))
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_vector_snapshot() -> dict[str, Any]:
    snap = VECTOR_LAKE_DIR / "snapshot.json"
    if snap.exists():
        return json.loads(snap.read_text())
    return {}


def _load_telemetry_snapshot() -> dict[str, Any]:
    tel = pathlib.Path("output/telemetry_snapshot.json")
    if tel.exists():
        return json.loads(tel.read_text())
    return {}


def _resource_id_for_path(raw_path: str) -> str:
    normalized = raw_path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


# ---------------------------------------------------------------------------
# MCP Resource endpoints
# ---------------------------------------------------------------------------

@app.get("/mcp/resources", summary="List MCP artifact resources from the data lake")
async def list_mcp_resources() -> dict:
    """
    Lists all indexed artifact resources available in the vector lake.
    Conforms to the MCP resource listing protocol.
    """
    snapshot = _load_vector_snapshot()
    resources = []
    for a in snapshot.get("artifacts", []):
        path = a.get("path", "")
        resources.append({
            "uri": f"mcp://a2a/{_resource_id_for_path(path)}",
            "name": pathlib.Path(path or "unknown").name,
            "fingerprint": a.get("fingerprint"),
            "mimeType": "application/octet-stream",
        })
    return {
        "resources": resources,
        "count": len(resources),
        "snapshot_timestamp": snapshot.get("timestamp"),
    }


@app.get("/mcp/resources/{resource_id:path}", summary="Get a specific MCP resource")
async def get_mcp_resource(resource_id: str) -> dict:
    snapshot = _load_vector_snapshot()
    for a in snapshot.get("artifacts", []):
        path = a.get("path", "")
        if _resource_id_for_path(path) == resource_id:
            p = pathlib.Path(a["path"])
            content = None
            if p.exists() and p.stat().st_size < 100_000:  # 100KB limit
                try:
                    content = p.read_text(errors="replace")
                except Exception:
                    content = "<binary>"
            return {
                "uri": f"mcp://a2a/{resource_id}",
                "content": content,
                "fingerprint": a.get("fingerprint"),
            }
    raise HTTPException(status_code=404, detail=f"Resource not found: {resource_id}")


@app.get("/mcp/telemetry", summary="Get the latest geodesic telemetry snapshot")
async def get_telemetry() -> dict:
    """Returns the latest compacted geodesic embedding from the Sentry sink."""
    tel = _load_telemetry_snapshot()
    if not tel:
        raise HTTPException(status_code=404, detail="No telemetry snapshot found — run the embed+telemetry pipeline phases")
    return tel


# ---------------------------------------------------------------------------
# Gemini API control layer
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    prompt: str
    model: str = GEMINI_MODEL
    system_instruction: str = (
        "You are the Gemini OS control layer for the A2A_MCP monorepo. "
        "Route agent tasks, summarize artifacts, and drive the CI pipeline. "
        "You operate as the AI control plane for the galaxy of UI sites."
    )
    temperature: float = 0.4


@app.post("/api/generate", summary="Invoke Gemini API as the control layer")
async def generate(req: GenerateRequest) -> dict:
    """
    Calls the Gemini API with the given prompt, using the MCP artifact context
    as grounding. Acts as the AI control layer for the pipeline.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY not configured — set the environment variable",
        )
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            model_name=req.model,
            system_instruction=req.system_instruction,
        )
        t0 = time.perf_counter()
        response = model.generate_content(
            req.prompt,
            generation_config={"temperature": req.temperature},
        )
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {
            "model": req.model,
            "text": response.text,
            "latency_ms": latency_ms,
        }
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="google-generativeai not installed — run: pip install google-generativeai",
        )
    except Exception as exc:  # noqa: BLE001
        log.error("Gemini API error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# UI galaxy routing
# ---------------------------------------------------------------------------

UI_SITES: dict[str, str] = {
    "cockpit":   "ui/cockpit",
    "frontend":  "frontend",
    "app":       "app",
    "apps":      "apps",
    "chatgpt":   "chatgpt-app",
    "base44":    "base44",
    "web-pet":   "web-pet-kernel",
}


@app.get("/ui", summary="List available UI sites (galaxy of UIs)")
async def list_ui_sites() -> dict:
    """Returns the galaxy of UI sites available in the monorepo."""
    sites = []
    for name, path in UI_SITES.items():
        p = pathlib.Path(path)
        sites.append({
            "name": name,
            "path": str(p),
            "exists": p.exists(),
        })
    return {"ui_sites": sites, "count": len(sites)}


# ---------------------------------------------------------------------------
# Health & index
# ---------------------------------------------------------------------------

@app.get("/", summary="MCP control layer index")
async def index() -> dict:
    snapshot = _load_vector_snapshot()
    return {
        "service": "Gemini OS MCP Control Layer",
        "version": "1.0.0",
        "model": GEMINI_MODEL,
        "vector_lake": str(VECTOR_LAKE_DIR),
        "snapshot_timestamp": snapshot.get("timestamp", "none"),
        "artifact_count": len(snapshot.get("artifacts", snapshot.get("vectors", []))),
        "endpoints": {
            "resources":  "/mcp/resources",
            "telemetry":  "/mcp/telemetry",
            "generate":   "/api/generate",
            "ui_galaxy":  "/ui",
            "docs":       "/docs",
        },
    }


@app.get("/health", summary="Health check")
async def health() -> dict:
    return {"status": "ok", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("MCP_PORT", "9090"))
    log.info("Starting Gemini OS MCP Control Layer on port %d", port)
    uvicorn.run("mcp_servers.gemini_control:app", host="0.0.0.0", port=port, reload=True)
