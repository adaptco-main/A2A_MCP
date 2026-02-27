from bootstrap import bootstrap_paths

bootstrap_paths()

try:
    from fastmcp import FastMCP
except ModuleNotFoundError:
    from mcp.server.fastmcp import FastMCP
from orchestrator.storage import SessionLocal
from schemas.database import ArtifactModel
import os

import requests

# Initialize FastMCP Server
mcp = FastMCP("A2A_Orchestrator")

@mcp.tool()
def get_artifact_trace(root_id: str):
    """Retrieves the full Research -> Code -> Test trace for a specific run."""
    db = SessionLocal()
    try:
        artifacts = db.query(ArtifactModel).filter(
            (ArtifactModel.id == root_id) | (ArtifactModel.parent_artifact_id == root_id)
        ).all()
        return [f"{a.agent_name}: {a.type} (ID: {a.id})" for a in artifacts]
    finally:
        db.close()

@mcp.tool()
def trigger_new_research(query: str):
    """Triggers the A2A pipeline for a new user query via the orchestrator."""
    api_base_url = os.getenv("MCP_API_BASE_URL", "http://localhost:8000").rstrip("/")
    timeout_seconds = float(os.getenv("MCP_API_TIMEOUT_SECONDS", "10"))
    response = requests.post(
        f"{api_base_url}/orchestrate",
        params={"user_query": query},
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    mcp.run()
