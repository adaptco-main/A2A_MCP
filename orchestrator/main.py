from fastapi import FastAPI, HTTPException
from typing import Dict
import uvicorn

# Import the schema and all three agents
from schemas.agent_artifacts import MCPArtifact
from agents.researcher import ResearcherAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent

app = FastAPI(title="A2A MCP Orchestrator")

# Initialize the agent fleet
researcher = ResearcherAgent()
coder = CoderAgent()
tester = TesterAgent()

# In-memory store for tracking the artifact chain
artifact_store: Dict[str, MCPArtifact] = {}

@app.post("/orchestrate")
async def orchestrate_full_flow(user_query: str):
    """
    The Full A2A Loop:
    1. Researcher -> Creates research_doc
    2. Coder -> Consumes research_doc, creates code_solution
    3. Tester -> Consumes code_solution, creates test_report
    """
    try:
        # STEP 1: Research
        res_art = await researcher.run(topic=user_query)
        artifact_store[res_art.artifact_id] = res_art

        # STEP 2: Development
        cod_art = await coder.run(research_artifact=res_art)
        artifact_store[cod_art.artifact_id] = cod_art

        # STEP 3: Quality Assurance
        tst_art = await tester.run(code_artifact=cod_art)
        artifact_store[tst_art.artifact_id] = tst_art

        return {
            "status": "A2A Workflow Complete",
            "pipeline_results": {
                "research": res_art.artifact_id,
                "coding": cod_art.artifact_id,
                "testing": tst_art.artifact_id
            },
            "test_summary": tst_art.content,
            "final_code": cod_art.content
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
