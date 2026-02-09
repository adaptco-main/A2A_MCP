from fastapi import FastAPI, HTTPException
from typing import List, Dict
import uuid

# Import the schema we defined earlier
# Assuming it's in a /schemas folder
from schemas.agent_artifacts import MCPArtifact, AgentTask

app = FastAPI(title="A2A MCP Orchestrator")

# In-memory store for tracking artifact history
artifact_store: Dict[str, MCPArtifact] = {}

@app.get("/")
async def root():
    return {"message": "A2A MCP Orchestrator is Online"}

@app.post("/orchestrate")
async def orchestrate_flow(user_query: str):
    """
    Main A2A Routing Logic:
    1. User -> Researcher (Task)
    2. Researcher -> Hub (Artifact)
    3. Hub + Artifact -> Coder (Context)
    4. Coder -> User (Solution)
    """
    try:
        # STEP 1: Trigger Researcher
        # In a real app, this would be an HTTP call to your Researcher Agent
        research_artifact = await simulate_agent_call(
            agent_name="Researcher",
            instruction=f"Research requirements for: {user_query}",
            artifact_type="research_doc"
        )
        store_artifact(research_artifact)

        # STEP 2: Trigger Coder using Researcher's output as Context
        coding_artifact = await simulate_agent_call(
            agent_name="Coder",
            instruction="Generate implementation based on the research context",
            context=research_artifact.content,
            artifact_type="code_solution"
        )
        store_artifact(coding_artifact)

        return {
            "status": "success",
            "final_solution": coding_artifact.content,
            "trace_id": coding_artifact.artifact_id,
            "steps_completed": ["research", "coding"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def simulate_agent_call(agent_name, instruction, context=None, artifact_type="text"):
    """
    Placeholder for actual A2A communication logic.
    Replace this with your LLM API calls or MCP Tool invocations.
    """
    return MCPArtifact(
        artifact_id=str(uuid.uuid4()),
        type=artifact_type,
        content=f"[{agent_name} Result] Processed: {instruction}. Context used: {context[:50] if context else 'None'}",
        metadata={"agent": agent_name}
    )

def store_artifact(artifact: MCPArtifact):
    artifact_store[artifact.artifact_id] = artifact

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
