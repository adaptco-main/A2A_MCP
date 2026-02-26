"""Deterministic repository snapshot ingestion utilities."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any
import numpy as np

# Note: TELEMETRY should be imported from orchestrator.metrics or handled via a placeholder if app.mcp_tooling is not yet fixed
try:
    from app.mcp_tooling import TELEMETRY
except ImportError:
    # Fallback for during merge/refactor
    class MockTelemetry:
        def start_timer(self): return 0
        def record_request_outcome(self, **kwargs): pass
        def observe_protected_ingestion_latency(self, *args, **kwargs): pass
    TELEMETRY = MockTelemetry()


def _deterministic_embedding(text: str, dimensions: int = 1536) -> list[float]:
    """Generate a deterministic pseudo-embedding for demonstration."""
    hash_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = np.random.default_rng(hash_val & 0xFFFFFFFF)
    return rng.standard_normal(dimensions).tolist()


@dataclass
class VectorNode:
    """Ingested node destined for vector storage."""

    node_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "text": self.text,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }


class VectorIngestionEngine:
    """Creates deterministic vector nodes from a repository snapshot."""

    def __init__(self, embedding_dim: int = 1536) -> None:
        self.embedding_dim = embedding_dim

    async def process_snapshot(
        self,
        snapshot_data: dict[str, Any],
        oidc_claims: dict[str, Any],
    ) -> list[dict[str, Any]]:
        repository = str(snapshot_data.get("repository", "")).strip()
        commit_sha = str(snapshot_data.get("commit_sha", "")).strip()
        actor = str(oidc_claims.get("actor", "unknown")).strip()

        telemetry_timer = TELEMETRY.start_timer()
        nodes: list[VectorNode] = []
        snippets = snapshot_data.get("code_snippets", [])
        for index, snippet in enumerate(snippets):
            file_path = str(snippet.get("file_path", f"snippet_{index}.py"))
            content = str(snippet.get("content", ""))
            text = f"[{file_path}]\n{content}"
            node_id = hashlib.sha256(f"{repository}:{commit_sha}:{file_path}".encode("utf-8")).hexdigest()[:24]
            nodes.append(
                VectorNode(
                    node_id=node_id,
                    text=text,
                    embedding=_deterministic_embedding(text, self.embedding_dim),
                    metadata={
                        "type": "code_solution",
                        "repository": repository,
                        "commit_sha": commit_sha,
                        "actor": actor,
                        "file_path": file_path,
                    },
                )
            )

        readme = str(snapshot_data.get("readme_content", "")).strip()
        if readme:
            node_id = hashlib.sha256(f"{repository}:{commit_sha}:README".encode("utf-8")).hexdigest()[:24]
            nodes.append(
                VectorNode(
                    node_id=node_id,
                    text=readme,
                    embedding=_deterministic_embedding(readme, self.embedding_dim),
                    metadata={
                        "type": "research_doc",
                        "repository": repository,
                        "commit_sha": commit_sha,
                        "actor": actor,
                        "file_path": "README.md",
                    },
                )
            )

        TELEMETRY.record_request_outcome(
            avatar_id=actor or "unknown",
            client_id=repository or "unknown",
            outcome="accepted",
        )
        TELEMETRY.observe_protected_ingestion_latency(telemetry_timer, client_id=repository or "unknown")
        return [node.to_dict() for node in nodes]


_KNOWLEDGE_STORE: dict[str, dict[str, Any]] = {}


async def upsert_to_knowledge_store(vector_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Insert/update nodes in an in-memory knowledge store."""
    for node in vector_nodes:
        _KNOWLEDGE_STORE[str(node["node_id"])] = node
    return {"count": len(vector_nodes)}


def get_knowledge_store() -> dict[str, dict[str, Any]]:
    """Expose current store for tests/inspection."""
    return dict(_KNOWLEDGE_STORE)
