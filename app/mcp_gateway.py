"""HTTP MCP gateway exposing native MCP transport and `/tools/call` compatibility."""

from __future__ import annotations

import os
from typing import Any

from bootstrap import bootstrap_paths

bootstrap_paths()

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from mcp.server.fastmcp import FastMCP

def call_tool_by_name(tool_name: str, arguments: dict, authorization_header: str | None = None):
    """Placeholder for calling a tool by name."""
    return "error: tool not found"

def register_tools(mcp):
    """Placeholder for registering tools."""
    pass


class ToolCallRequest(BaseModel):
    """Compatibility payload for legacy `/tools/call` clients."""

    tool_name: str = Field(..., min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


mcp = FastMCP("A2A_Orchestrator_HTTP")
register_tools(mcp)

mcp_http_app = mcp.http_app(transport="streamable-http", path="/")
app = FastAPI(
    title="A2A MCP Gateway",
    version="1.0.0",
    lifespan=mcp_http_app.lifespan,
)

# Path `/mcp` is preserved externally while FastMCP handles root path internally.
app.mount("/mcp", mcp_http_app)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/tools/call")
async def tools_call(
    payload: ToolCallRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> dict[str, Any]:
    try:
        result = call_tool_by_name(
            tool_name=payload.tool_name,
            arguments=payload.arguments,
            authorization_header=authorization,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=f"invalid arguments for {payload.tool_name}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - surfaced to client for compatibility debugging.
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    ok = not (isinstance(result, str) and result.lower().startswith("error:"))
    return {
        "tool_name": payload.tool_name,
        "ok": ok,
        "result": result,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.mcp_gateway:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=False,
    )
