# tests/test_mcp_agents.py
import ast
from unittest.mock import patch

import pytest
from fastmcp import Client

from knowledge_ingestion import app_ingest


@pytest.fixture
def mock_snapshot():
    return {
        "repository": "adaptco/A2A_MCP",
        "commit_sha": "abc123",
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
    """Verifies that the agent accepts data when OIDC claims are valid."""
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
    """Verifies that repository provenance is bound to verified token claims."""
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
async def test_ingestion_rejects_invalid_token(mock_snapshot):
    """Verifies that invalid tokens cannot bypass authentication."""
    with patch("knowledge_ingestion.verify_github_oidc_token", side_effect=ValueError("Invalid OIDC token")):
        async with Client(app_ingest) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "ingest_repository_data",
                    {
                        "snapshot": mock_snapshot,
                        "authorization": "Bearer invalid",
                    },
                )
