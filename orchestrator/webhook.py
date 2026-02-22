<<<<<<< Updated upstream
# inside A2A_MCP/orchestrator/webhook.py
from fastapi import FastAPI, HTTPException, Body
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path
=======
import time
from fastapi import FastAPI, HTTPException, Body, Response
from prometheus_client import generate_latest, REGISTRY
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path
from orchestrator.storage import save_plan_state
from orchestrator.intent_engine import IntentEngine
from orchestrator.metrics import (
    record_request, record_plan_ingress, record_verification
)
>>>>>>> Stashed changes

app = FastAPI(...)

# in-memory map (replace with DB-backed persistence or plan state store in prod)
PLAN_STATE_MACHINES = {}

@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    """
    Accepts:
      - plan_id: optional canonical id
      - plan_file_path: optional file path that contains plan id in its basename
    Prioritizes plan_id if given; otherwise tries to extract id from plan_file_path.
    """
    plan_id = payload.get("plan_id")
<<<<<<< Updated upstream
    if not plan_id:
        plan_file_path = payload.get("plan_file_path", "")
        plan_id = extract_plan_id_from_path(plan_file_path)
    if not plan_id:
        raise HTTPException(status_code=400, detail="Unable to determine plan_id; provide plan_id or plan_file_path")
    # Ensure plan_id is sanitized
    plan_id = plan_id.strip()
    # Create or reuse an FSM for plan
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        # create the state machine; you might pass persistence hook here
        from orchestrator.stateflow import StateMachine
        sm = StateMachine(max_retries=3)
        sm.plan_id = plan_id
        PLAN_STATE_MACHINES[plan_id] = sm

    rec = sm.trigger("OBJECTIVE_INGRESS")
    return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}
=======
    if plan_id:
        return str(plan_id).strip()

    plan_file_path = payload.get("plan_file_path", "")
    extracted = extract_plan_id_from_path(plan_file_path)
    return extracted.strip() if extracted else None


async def _plan_ingress_impl(path_plan_id: str | None, payload: dict):
    """
    Accepts either:
      - /plans/ingress with JSON body: {"plan_id": "..."} or {"plan_file_path": "..."}
      - /plans/{plan_id}/ingress with optional JSON body
    """
    start = time.time()
    try:
        plan_id = _resolve_plan_id(path_plan_id, payload or {})
        if not plan_id:
            record_plan_ingress('error')
            raise HTTPException(status_code=400, detail="Unable to determine plan_id; provide plan_id or plan_file_path")

        sm = PLAN_STATE_MACHINES.get(plan_id)
        if not sm:
            sm = StateMachine(max_retries=3, persistence_callback=persistence_callback)
            sm.plan_id = plan_id
            PLAN_STATE_MACHINES[plan_id] = sm
            record_plan_ingress('created')
        else:
            record_plan_ingress('resumed')

        rec = sm.trigger("OBJECTIVE_INGRESS")
        duration_ms = (time.time() - start) * 1000
        record_request(result='success', duration_ms=duration_ms)
        
        return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        record_request(result='error', duration_ms=duration_ms, halt_reason='exception')
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    return await _plan_ingress_impl(None, payload)


@app.post("/plans/{plan_id}/ingress")
async def plan_ingress_by_id(plan_id: str, payload: dict = Body(default={})):
    return await _plan_ingress_impl(plan_id, payload)


@app.post("/orchestrate")
async def orchestrate(user_query: str):
    """
    Triggers the full A2A pipeline (Managing->Orchestration->Architecture->Coder->Tester).
    Matches the contract expected by mcp_server.py.
    """
    start = time.time()
    engine = IntentEngine()
    
    try:
        result = await engine.run_full_pipeline(description=user_query, requester="api_user")
        
        # Summarize results
        summary = {
            "status": "A2A Workflow Complete",
            "success": result.success,
            "pipeline_results": {
                "plan_id": result.plan.plan_id,
                "blueprint_id": result.blueprint.plan_id,
                "code_artifacts": [a.artifact_id for a in result.code_artifacts],
            },
            # Return last code artifact content as 'final_code' for the MCP tool
            "final_code": result.code_artifacts[-1].content if result.code_artifacts else None,
            "test_summary": f"Passed: {sum(1 for v in result.test_verdicts if v['status'] == 'PASS')}/{len(result.test_verdicts)}"
        }
        
        duration_ms = (time.time() - start) * 1000
        record_request(result='success', duration_ms=duration_ms)
        return summary
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        record_request(result='error', duration_ms=duration_ms, halt_reason='exception')
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """
    Health check endpoint. Returns application status.
    Preserves existing JSON contract (unchanged for MCP/tools compatibility).
    """
    return {"status": "healthy", "service": "A2A_MCP_Orchestrator"}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    Exposes request counters, latency histograms, and verification results.
    
    Metrics exposed:
    - a2a_orchestrator_requests_total{result="success|halt|error"}
    - a2a_orchestrator_plan_ingress_total{status="created|resumed|error"}
    - a2a_orchestrator_verification_results_total{valid="true|false"}
    - a2a_orchestrator_duration_ms_bucket{le="...", result="..."}
    - a2a_orchestrator_system_halt_total{reason="..."}
    """
    metrics = generate_latest(REGISTRY)
    return Response(content=metrics, media_type="text/plain; version=0.0.4")
>>>>>>> Stashed changes
