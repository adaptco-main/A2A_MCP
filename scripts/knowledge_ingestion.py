from __future__ import annotations


from typing import Any

from app.security.oidc import (
    OIDCAuthError,
    OIDCClaimError,
    enforce_avatar_ingest_allowlists,
    extract_bearer_token,
    get_request_correlation_id,
    validate_startup_oidc_requirements,
    verify_bearer_token,
)
from fastmcp import FastMCP

from app.mcp_tooling import (
    ingest_repository_data as protected_ingest_repository_data,
    verify_github_oidc_token,
)

app_ingest = FastMCP("knowledge-ingestion")
validate_startup_oidc_requirements()


def verify_github_oidc_token(token: str, request_id: str | None = None) -> dict[str, Any]:
    correlation_id = request_id or get_request_correlation_id()
    return verify_bearer_token(token, request_id=correlation_id)


@app_ingest.tool()
def ingest_repository_data(snapshot: dict[str, Any], authorization: str, request_id: str | None = None) -> str:
    correlation_id = request_id or get_request_correlation_id()

    try:
        token = extract_bearer_token(authorization)
        claims = verify_github_oidc_token(token, request_id=correlation_id)
    except OIDCAuthError:
        return f"error: unauthorized (request_id={correlation_id})"
    except OIDCClaimError:
        return f"error: forbidden (request_id={correlation_id})"

    repository = str(claims.get("repository", "")).strip()
    snapshot_repository = str(snapshot.get("repository", "")).strip()
    if snapshot_repository and snapshot_repository != repository:
        return f"error: repository claim mismatch (request_id={correlation_id})"

    route = str(snapshot.get("route", "")).strip().lower()
    if route == "avatar-ingest":
        try:
            enforce_avatar_ingest_allowlists(claims, request_id=correlation_id)
        except OIDCClaimError:
            return f"error: forbidden (request_id={correlation_id})"

    return f"success: ingested repository {repository} (request_id={correlation_id})"
