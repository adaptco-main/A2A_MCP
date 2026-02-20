from __future__ import annotations

from typing import Any

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:
    from mcp.server.fastmcp import FastMCP

from app.mcp_tooling import (
    ingest_repository_data_impl,
    ingest_worldline_block_impl,
)
from app.security.oidc import verify_github_oidc_token as _verify_github_oidc_token

app_ingest = FastMCP("knowledge-ingestion")


def verify_github_oidc_token(token: str) -> dict[str, Any]:
    """Compatibility wrapper for tests that patch this symbol directly."""
    return _verify_github_oidc_token(token)


@app_ingest.tool(name="ingest_repository_data")
def ingest_repository_data(snapshot: dict[str, Any], authorization: str) -> str:
    return ingest_repository_data_impl(
        snapshot=snapshot,
        authorization=authorization,
        verifier=verify_github_oidc_token,
    )


@app_ingest.tool(name="ingest_worldline_block")
def ingest_worldline_block(worldline_block: dict[str, Any], authorization: str) -> str:
    """Ingest a multimodal worldline block for MCP orchestration."""
    return ingest_worldline_block_impl(
        worldline_block=worldline_block,
        authorization=authorization,
        verifier=verify_github_oidc_token,
    )
