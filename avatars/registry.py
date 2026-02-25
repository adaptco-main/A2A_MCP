import hashlib
import logging
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field

from oidc_token import verify_github_oidc_token

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_ingest = FastAPI(title="A2A Vector Ingestion Service")

class VectorNode(BaseModel):
    node_id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()

def _deterministic_embedding(text: str, dim: int) -> List[float]:
    """
    Generate a deterministic pseudo-embedding for demonstration.
    In production, replace this with a call to an embedding model (e.g., OpenAI, HuggingFace).
    """
    hash_val = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)
    rng = np.random.default_rng(hash_val & 0xFFFFFFFF)
    return rng.standard_normal(dim).tolist()

class VectorIngestionEngine:
    """Creates deterministic vector nodes from a repository snapshot."""

    def __init__(self, embedding_dim: int = 1536) -> None:
        self.embedding_dim = embedding_dim

    async def process_snapshot(
        self,
        snapshot_data: Dict[str, Any],
        oidc_claims: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        repository = str(snapshot_data.get("repository", "unknown-repo")).strip()
        commit_sha = str(snapshot_data.get("commit_sha", "head")).strip()
        actor = str(oidc_claims.get("actor", oidc_claims.get("sub", "unknown"))).strip()

        nodes: List[VectorNode] = []
        
        # Process Code Snippets
        snippets = snapshot_data.get("code_snippets", [])
        for index, snippet in enumerate(snippets):
            file_path = str(snippet.get("file_path", f"snippet_{index}.py"))
            content = str(snippet.get("content", ""))
            if not content:
                continue
                
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

        # Process README/Documentation
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
_KNOWLEDGE_STORE: Dict[str, Dict[str, Any]] = {}

async def upsert_to_knowledge_store(vector_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Insert/update nodes in an in-memory knowledge store."""
    for node in vector_nodes:
        _KNOWLEDGE_STORE[str(node["node_id"])] = node
    return {"count": len(vector_nodes), "status": "success"}

@app_ingest.post("/ingest")
async def ingest_repository(snapshot: Dict[str, Any], authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid OIDC Token")
    
    token = authorization.split(" ")[1]
    try:
        claims = verify_github_oidc_token(token)
        vector_nodes = await vector_engine.process_snapshot(snapshot, claims)
        return await upsert_to_knowledge_store(vector_nodes)
    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")