"""Shared MCP tool implementations for stdio and HTTP runtimes."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable

import requests
import torch

from a2a_mcp.mcp_core import MCPCore
from app.security.oidc import parse_bearer_token, verify_github_oidc_token
from orchestrator.storage import SessionLocal
from schemas.database import ArtifactModel

ToolCallable = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    """Tool metadata shared by MCP server and compatibility API."""

    name: str
    func: ToolCallable
    protected: bool = False


def _coerce_embedding_vector(raw: list[float] | tuple[float, ...], input_dim: int) -> torch.Tensor:
    values = list(raw)
    if len(values) != int(input_dim):
        raise ValueError(f"Expected embedding length {input_dim}, received {len(values)}")
    return torch.tensor(values, dtype=torch.float32).view(1, int(input_dim))


def get_artifact_trace(root_id: str) -> list[str]:
    """Retrieve the full Research -> Code -> Test trace for a specific run."""
    db = SessionLocal()
    try:
        artifacts = db.query(ArtifactModel).filter(
            (ArtifactModel.id == root_id) | (ArtifactModel.parent_artifact_id == root_id)
        ).all()
        return [f"{a.agent_name}: {a.type} (ID: {a.id})" for a in artifacts]
    finally:
        db.close()


def trigger_new_research(query: str) -> dict[str, Any]:
    """Trigger the A2A pipeline for a new user query via orchestrator API."""
    orchestrator_url = os.getenv("ORCHESTRATOR_API_URL", "http://localhost:8000").rstrip("/")
    endpoint = f"{orchestrator_url}/orchestrate"
    response = requests.post(endpoint, params={"user_query": query}, timeout=30)
    response.raise_for_status()
    return response.json()


def ingest_repository_data_impl(
    snapshot: dict[str, Any],
    authorization: str,
    verifier: Callable[[str], dict[str, Any]] | None = None,
) -> str:
    """Ingest repository snapshot payload under optional strict OIDC validation."""
    if not authorization.startswith("Bearer "):
        return "error: missing bearer token"

    token = parse_bearer_token(authorization)
    claims = (verifier or verify_github_oidc_token)(token)
    repository = str(snapshot.get("repository", "")).strip()

    if repository and claims.get("repository") and claims["repository"] != repository:
        return "error: repository claim mismatch"

    return f"success: ingested repository {repository}"


def ingest_worldline_block_impl(
    worldline_block: dict[str, Any],
    authorization: str,
    verifier: Callable[[str], dict[str, Any]] | None = None,
) -> str:
    """Ingest multimodal worldline block payload under optional strict OIDC validation."""
    if not authorization.startswith("Bearer "):
        return "error: missing bearer token"

    token = parse_bearer_token(authorization)
    claims = (verifier or verify_github_oidc_token)(token)

    snapshot = worldline_block.get("snapshot", {})
    repository = str(snapshot.get("repository", "")).strip()
    if repository and claims.get("repository") and claims["repository"] != repository:
        return "error: repository claim mismatch"

    infra = worldline_block.get("infrastructure_agent", {})
    if not isinstance(infra, dict):
        return "error: invalid infrastructure_agent payload"

    required = ["embedding_vector", "token_stream", "artifact_clusters", "lora_attention_weights"]
    missing = [field for field in required if field not in infra]
    if missing:
        return f"error: missing required fields: {', '.join(missing)}"

    return (
        "success: ingested worldline block "
        f"for {repository or 'unknown-repository'} "
        f"with {len(infra.get('token_stream', []))} tokens"
    )


def ingest_repository_data(snapshot: dict[str, Any], authorization: str) -> str:
    """Default MCP tool wrapper for repository ingestion."""
    return ingest_repository_data_impl(snapshot=snapshot, authorization=authorization)


def ingest_worldline_block(worldline_block: dict[str, Any], authorization: str) -> str:
    """Default MCP tool wrapper for worldline ingestion."""
    return ingest_worldline_block_impl(worldline_block=worldline_block, authorization=authorization)


def run_mcp_core(
    namespaced_embedding: list[float],
    input_dim: int = 4096,
    hidden_dim: int = 128,
    n_roles: int = 32,
) -> dict[str, Any]:
    """Execute foundation-model middleware computation on a namespaced embedding."""
    model = MCPCore(input_dim=input_dim, hidden_dim=hidden_dim, n_roles=n_roles)
    tensor = _coerce_embedding_vector(namespaced_embedding, input_dim=input_dim)
    with torch.no_grad():
        result = model(tensor)

    return {
        "processed_embedding": result.processed_embedding.squeeze(0).detach().cpu().tolist(),
        "arbitration_scores": result.arbitration_scores.detach().cpu().tolist(),
        "protocol_features": result.protocol_features,
        "execution_hash": result.execution_hash,
    }


def compute_protocol_similarity(
    embedding_a: list[float],
    embedding_b: list[float],
    input_dim: int = 4096,
    hidden_dim: int = 128,
    n_roles: int = 32,
) -> float:
    """Compute namespace-safe protocol similarity between two embeddings."""
    model = MCPCore(input_dim=input_dim, hidden_dim=hidden_dim, n_roles=n_roles)
    emb_a = _coerce_embedding_vector(embedding_a, input_dim=input_dim)
    emb_b = _coerce_embedding_vector(embedding_b, input_dim=input_dim)
    with torch.no_grad():
        return model.compute_protocol_similarity(emb_a, emb_b)


TOOL_SPECS: tuple[ToolSpec, ...] = (
    ToolSpec(name="get_artifact_trace", func=get_artifact_trace),
    ToolSpec(name="trigger_new_research", func=trigger_new_research),
    ToolSpec(name="ingest_repository_data", func=ingest_repository_data, protected=True),
    ToolSpec(name="ingest_worldline_block", func=ingest_worldline_block, protected=True),
    ToolSpec(name="run_mcp_core", func=run_mcp_core),
    ToolSpec(name="compute_protocol_similarity", func=compute_protocol_similarity),
)

TOOL_MAP: dict[str, ToolSpec] = {tool.name: tool for tool in TOOL_SPECS}


def register_tools(mcp: Any) -> None:
    """Register shared tools on FastMCP instance."""
    for spec in TOOL_SPECS:
        mcp.tool(name=spec.name)(spec.func)


def call_tool_by_name(
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    authorization_header: str | None = None,
) -> Any:
    """Invoke a shared MCP tool by name for `/tools/call` compatibility endpoint."""
    spec = TOOL_MAP.get(tool_name)
    if spec is None:
        raise KeyError(f"unknown tool: {tool_name}")

    payload = dict(arguments or {})
    if spec.protected and "authorization" not in payload and authorization_header:
        payload["authorization"] = authorization_header
    if spec.protected and "authorization" not in payload:
        raise ValueError("Missing authorization for protected tool")

    return spec.func(**payload)
