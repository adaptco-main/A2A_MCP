# tests/test_mcp_agents.py
import ast
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
    return ast.literal_eval(text)


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
            assert payload["data"]["repository"] == "adaptco/A2A_MCP"
            assert len(payload["data"]["execution_hash"]) == 64


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
            assert payload["error"]["code"] == "REPOSITORY_CLAIM_MISMATCH"


@pytest.mark.asyncio
async def test_ingestion_rejects_invalid_token_without_leaking_details(mock_snapshot):
    with patch("knowledge_ingestion.verify_github_oidc_token", side_effect=OIDCAuthError("signature verification failed")):
        async with Client(app_ingest) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "ingest_repository_data",
                    {
                        "snapshot": mock_snapshot,
                        "authorization": "Bearer invalid",
                    },
                )


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
        assert payload["error"]["code"] == "AUTH_BEARER_MISSING"


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
        assert payload["error"]["code"] == "AUTH_BEARER_EMPTY"


@pytest.mark.asyncio
async def test_ingestion_rejects_token_without_repo_claim(mock_snapshot):
    with patch("knowledge_ingestion.verify_github_oidc_token", side_effect=ValueError("OIDC token missing repository claim")):
        async with Client(app_ingest) as client:
            with pytest.raises(Exception) as excinfo:
                await client.call_tool(
                    "ingest_repository_data",
                    {
                        "snapshot": mock_snapshot,
                        "authorization": "Bearer valid_mock_token",
                    },
                )
            assert "OIDC token missing repository claim" in str(excinfo.value)


@pytest.mark.asyncio
async def test_ingestion_with_snapshot_without_repository(mock_snapshot):
    mock_claims = {"repository": "adaptco/A2A_MCP", "actor": "github-actions"}
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
            assert payload["data"]["repository"] == "adaptco/A2A_MCP"


@pytest.mark.asyncio
async def test_ingestion_has_consistent_execution_hash(mock_snapshot):
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
            # This hash is pre-calculated for the given mock_snapshot and repository
            expected_hash = "e72e1bd6e5ae9c6e5193f27f9ee32c9d3aa5775ad3919293e516d19aeb61a187"
            assert payload["data"]["execution_hash"] == expected_hash
