import hashlib
from typing import Any
from pydantic import BaseModel, Field
import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends
from oidc_token import verify_github_oidc_token

app_ingest = FastAPI()

class VectorNode(BaseModel):
    node_id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

def _deterministic_embedding(text: str, dim: int) -> list[float]:
    """Generate a deterministic pseudo-embedding for demonstration."""
    hash_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = np.random.default_rng(hash_val & 0xFFFFFFFF)
    return rng.standard_normal(dim).tolist()

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

        return [node.to_dict() for node in nodes]

vector_engine = VectorIngestionEngine()

@app_ingest.post("/ingest")
async def ingest_repository(snapshot: dict, authorization: str = Header(None)):
    """Authenticated endpoint that indexes repository snapshots into Vector DB."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing OIDC Token")
    
    token = authorization.split(" ")[1]
    try:
        # 1. Validate A2A Proof (Handshake)
        claims = verify_github_oidc_token(token)
        
        # 2. Process & Embed (Phase 3 Integration)
        vector_nodes = await vector_engine.process_snapshot(snapshot, claims)
        
        # 3. Persistence
        result = await upsert_to_knowledge_store(vector_nodes)
        
        return result

_KNOWLEDGE_STORE: dict[str, dict[str, Any]] = {}


async def upsert_to_knowledge_store(vector_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Insert/update nodes in an in-memory knowledge store."""
    for node in vector_nodes:
        _KNOWLEDGE_STORE[str(node["node_id"])] = node
    return {"count": len(vector_nodes)}


def get_knowledge_store() -> dict[str, dict[str, Any]]:
    """Expose current store for tests/inspection."""
    return dict(_KNOWLEDGE_STORE)
