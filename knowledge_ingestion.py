"""Knowledge ingestion MCP tool entrypoint."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from app.mcp_tooling import ingest_repository_data as protected_ingest_repository_data
from app.mcp_tooling import verify_github_oidc_token

app_ingest = FastMCP("knowledge-ingestion")


@app_ingest.tool()
def ingest_repository_data(snapshot: dict[str, Any], authorization: str) -> dict[str, Any]:
    return protected_ingest_repository_data(
        snapshot=snapshot,
        authorization=authorization,
        verifier=verify_github_oidc_token,
    )
