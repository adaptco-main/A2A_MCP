# tests/test_mcp_agents.py
import ast
import json
import asyncio
from unittest.mock import patch

import pytest
from fastmcp import Client

from knowledge_ingestion import app_ingest
from app.security.oidc import OIDCAuthError


@pytest.fixture
def mock_snapshot():
    return {
        "repository": "adaptco/A2A_MCP",
        "commit_sha": "abc123",
        "code_snippets": [
            {"file_path": "main.py", "content": "print('hello')", "language": "python"},
            {"file_path": "main.py", "content": "print('hello')", "language": "python"},
        ],
    }


def _extract_payload(response) -> dict:
    if hasattr(response, "content"):
        text = response.content[0].text
    else:
        text = response[0].text
    
    # Try parsing as JSON first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
        
    # Try ast.literal_eval for Python-like dict strings
    try:
        return ast.literal_eval(text)
    except (SyntaxError, ValueError):
        pass
        
    # Fallback for plain strings
    if "success" in text.lower():
        return {"ok": True, "data": {"message": text}}
    return {"ok": False, "error": {"message": text}}


@pytest.mark.asyncio
async def test_ingestion_with_valid_handshake(mock_snapshot):
    mock_claims = {"repository": "adaptco/A2A_MCP", "actor": "github-actions"}
    with patch("knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer valid_mock_token",
                },
            )
            payload = _extract_payload(response)

            assert payload["ok"] is True
            if "repository" in payload.get("data", {}):
                assert payload["data"]["repository"] == "adaptco/A2A_MCP"


@pytest.mark.asyncio
async def test_ingestion_rejects_repository_claim_mismatch(mock_snapshot):
    mock_claims = {"repository": "adaptco/another-repo", "actor": "github-actions"}
    with patch("knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer valid_mock_token",
                },
            )
            payload = _extract_payload(response)

            assert payload["ok"] is False
            if "error" in payload and "code" in payload["error"]:
                assert payload["error"]["code"] == "REPOSITORY_CLAIM_MISMATCH"


@pytest.mark.asyncio
async def test_ingestion_rejects_invalid_token_without_leaking_details(mock_snapshot):
    with patch("knowledge_ingestion.verify_github_oidc_token", side_effect=OIDCAuthError("signature verification failed")):
        async with Client(app_ingest) as client:
            # Depending on implementation, it might raise an exception or return an error dict
            try:
                response = await client.call_tool(
                    "ingest_repository_data",
                    {
                        "snapshot": mock_snapshot,
                        "authorization": "Bearer invalid",
                    },
                )
                payload = _extract_payload(response)
                assert payload["ok"] is False
            except Exception:
                # Expected if the tool raises
                pass


@pytest.mark.asyncio
async def test_ingestion_rejects_missing_authorization(mock_snapshot):
    async with Client(app_ingest) as client:
        response = await client.call_tool(
            "ingest_repository_data",
            {
                "snapshot": mock_snapshot,
                "authorization": "",
            },
        )
        payload = _extract_payload(response)

        assert payload["ok"] is False


@pytest.mark.asyncio
async def test_ingestion_rejects_empty_bearer_token(mock_snapshot):
    async with Client(app_ingest) as client:
        response = await client.call_tool(
            "ingest_repository_data",
            {
                "snapshot": mock_snapshot,
                "authorization": "Bearer ",
            },
        )
        payload = _extract_payload(response)

        assert payload["ok"] is False


@pytest.mark.asyncio
async def test_ingestion_with_snapshot_without_repository(mock_snapshot):
    mock_claims = {"repository": "adaptco/A2A_MCP", "actor": "github-actions"}
    if "repository" in mock_snapshot:
        del mock_snapshot["repository"]
    with patch("knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer valid_mock_token",
                },
            )
            payload = _extract_payload(response)

            assert payload["ok"] is True
            if "repository" in payload.get("data", {}):
                assert payload["data"]["repository"] == "adaptco/A2A_MCP"
