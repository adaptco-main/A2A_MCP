import pytest

from app.mcp_tooling import call_tool_by_name


@pytest.mark.asyncio
async def test_call_tool_by_name_returns_correlation_id_for_unauthorized(monkeypatch):
    monkeypatch.setenv("OIDC_ENFORCE", "true")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer")
    monkeypatch.setenv("OIDC_AUDIENCE", "aud")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://jwks")

    response = await call_tool_by_name({}, "missing", {}, headers={"x-request-id": "req-1"})
    assert response == {"error": "tool_not_found", "request_id": "req-1"}


@pytest.mark.asyncio
async def test_avatar_ingest_enforces_allowlists(monkeypatch):
    monkeypatch.setenv("OIDC_ENFORCE", "true")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer")
    monkeypatch.setenv("OIDC_AUDIENCE", "aud")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://jwks")
    monkeypatch.setenv("OIDC_AVATAR_REPOSITORY_ALLOWLIST", "allowed/repo")
    monkeypatch.setenv("OIDC_AVATAR_ACTOR_ALLOWLIST", "allowed-actor")

    async def avatar_ingest_tool(snapshot):
        return snapshot

    # monkeypatch verifier to avoid network
    import app.mcp_tooling as tooling

    monkeypatch.setattr(tooling, "verify_bearer_token", lambda token, request_id: {"repository": "other/repo", "actor": "allowed-actor"})

    response = await call_tool_by_name(
        {"avatar-ingest-snapshot": avatar_ingest_tool},
        "avatar-ingest-snapshot",
        {"snapshot": {}},
        headers={"Authorization": "Bearer token", "x-request-id": "req-2"},
    )
    assert response == {"error": "forbidden", "request_id": "req-2"}
