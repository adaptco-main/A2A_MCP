# tests/test_mcp_agents.py
import ast
from unittest.mock import patch

import pytest
from fastmcp import Client

from knowledge_ingestion import app_ingest
from unittest.mock import patch

from app.security.oidc import OIDCAuthError



@pytest.fixture
def mock_snapshot():
    return {
        "repository": "adaptco/A2A_MCP",
        "commit_sha": "abc123",
        "code_snippets": [{"file_path": "main.py", "content": "print('hello')", "language": "python"}],
        "code_snippets": [{"file_path": "main.py", "content": "print('hello')", "language": "python"}],
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
    with patch("scripts.knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):

    with patch("knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer valid_mock_token",
                    "request_id": "req-123",
                },
            )
            text = response.content[0].text if hasattr(response, "content") else response[0].text
            assert "success" in text
            assert "adaptco/A2A_MCP" in text
            assert "request_id=req-123" in text
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
    with patch("scripts.knowledge_ingestion.verify_github_oidc_token", return_value=mock_claims):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer valid_mock_token",
                    "request_id": "req-456",
                },
            )
            text = response.content[0].text if hasattr(response, "content") else response[0].text
            assert text == "error: repository claim mismatch (request_id=req-456)"
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
    with patch("scripts.knowledge_ingestion.verify_github_oidc_token", side_effect=OIDCAuthError("signature verification failed")):
        async with Client(app_ingest) as client:
            response = await client.call_tool(
                "ingest_repository_data",
                {
                    "snapshot": mock_snapshot,
                    "authorization": "Bearer invalid",
                    "request_id": "req-789",
                },
            )
            text = response.content[0].text if hasattr(response, "content") else response[0].text
            assert text == "error: unauthorized (request_id=req-789)"
            assert "signature verification failed" not in text
            with pytest.raises(Exception):
                await client.call_tool(
                    "ingest_repository_data",
                    {
                        "snapshot": mock_snapshot,
                        "authorization": "Bearer invalid",
                    },
                )
