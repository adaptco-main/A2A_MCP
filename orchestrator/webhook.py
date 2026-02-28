from __future__ import annotations

import uuid
from typing import Optional

from fastapi import Body, FastAPI, Header, HTTPException

from orchestrator.intent_engine import IntentEngine
from orchestrator.runtime_bridge import (
    HandshakeInitRequest,
    build_handshake_bundle,
    fingerprint_secret,
)
from orchestrator.stateflow import StateMachine
from orchestrator.storage import DBManager, save_plan_state
from orchestrator.utils import extract_plan_id_from_path

app = FastAPI(title="A2A MCP Webhook")

# in-memory map (replace with DB-backed persistence or plan state store in prod)
PLAN_STATE_MACHINES = {}
RELEASE_JOBS = {}
CI_CD_MONITOR = None
WEBHOOK_SHARED_SECRET = ""
GITHUB_WEBHOOK_SECRET = ""

import asyncio
import hmac
import hashlib
from fastapi import Request

@app.post("/webhooks/github/actions")
async def github_actions_webhook(
    request: Request,
    x_github_event: str = Header(default=""),
    x_hub_signature_256: str = Header(default=""),
    x_webhook_token: str = Header(default="")
):
    if WEBHOOK_SHARED_SECRET and x_webhook_token != WEBHOOK_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    body = await request.body()
    
    if GITHUB_WEBHOOK_SECRET:
        if not x_hub_signature_256:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        expected_mac = hmac.new(
            GITHUB_WEBHOOK_SECRET.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        provided_mac = x_hub_signature_256.split("=")[-1]
        if not hmac.compare_digest(expected_mac, provided_mac):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    snapshot = {}
    if CI_CD_MONITOR:
        snapshot = CI_CD_MONITOR.ingest_github_workflow_event(payload)
    
    return {"status": "ingested", "snapshot": snapshot}


@app.get("/cicd/status/{sha}")
async def get_cicd_status(sha: str):
    if CI_CD_MONITOR:
        status = CI_CD_MONITOR.get_commit_status(sha)
        return status
    return {"ready_for_release": False}


async def _run_release_job(release_id: str, payload: dict, provider: str, event_type: str):
    try:
        engine = _get_engine()
        result = await engine.run_release_workflow_from_webhook(payload, provider, event_type)
        RELEASE_JOBS[release_id] = {"status": "completed", "result": result}
    except Exception as exc:
        RELEASE_JOBS[release_id] = {"status": "failed", "error": str(exc)}


@app.post("/webhooks/release")
async def release_webhook(
    request: Request,
    x_webhook_provider: str = Header(default="github"),
    x_webhook_event: str = Header(default="release"),
    x_webhook_token: str = Header(default="")
):
    if WEBHOOK_SHARED_SECRET and x_webhook_token != WEBHOOK_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid token")

    payload = await request.json()
    release_id = f"rel-{uuid.uuid4().hex[:8]}"
    RELEASE_JOBS[release_id] = {"status": "running"}
    
    # Run the job in background
    asyncio.create_task(_run_release_job(release_id, payload, x_webhook_provider, x_webhook_event))
    
    return {"status": "accepted", "release_id": release_id}


@app.get("/webhooks/release/{release_id}")
async def get_release_job_status(release_id: str):
    if release_id not in RELEASE_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    return RELEASE_JOBS[release_id]

def _get_engine():
    # Helper to get the intent engine, intended to be mocked in tests
    return IntentEngine()

def persistence_callback(plan_id: str, state_dict: dict) -> None:
    """Callback to persist FSM state to database."""
    try:
        save_plan_state(plan_id, state_dict)
    except Exception as exc:  # pragma: no cover - best effort persistence
        print(f"Warning: Failed to persist plan state for {plan_id}: {exc}")


def _resolve_plan_id(path_plan_id: str | None, payload: dict) -> str | None:
    if path_plan_id:
        return path_plan_id.strip()

    plan_id = payload.get("plan_id")
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
    plan_id = _resolve_plan_id(path_plan_id, payload or {})
    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine plan_id; provide plan_id or plan_file_path",
        )

    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        sm = StateMachine(max_retries=3, persistence_callback=persistence_callback)
        sm.plan_id = plan_id
        PLAN_STATE_MACHINES[plan_id] = sm

    rec = sm.trigger("OBJECTIVE_INGRESS")
    return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}


@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    return await _plan_ingress_impl(None, payload)


@app.post("/ingress")
async def plan_ingress_compat(payload: dict = Body(...)):
    return await _plan_ingress_impl(None, payload)


@app.post("/plans/{plan_id}/ingress")
async def plan_ingress_by_id(plan_id: str, payload: dict = Body(default={})):
    return await _plan_ingress_impl(plan_id, payload)


@app.post("/handshake/init")
async def initialize_handshake(
    payload: HandshakeInitRequest = Body(...),
    x_api_key: Optional[str] = Header(default=None),
):
    """
    Initialize MCP handshake with full state payload and runtime assignment
    bridge artifact generation.
    """
    api_key = (x_api_key or payload.mcp.api_key or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required for MCP handshake initialization",
        )

    api_key_fingerprint = fingerprint_secret(api_key)
    plan_id = (payload.plan_id or "").strip() or f"plan-{uuid.uuid4().hex[:10]}"
    handshake_id = f"hs-{uuid.uuid4().hex[:12]}"

    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        sm = StateMachine(max_retries=3, persistence_callback=persistence_callback)
        sm.plan_id = plan_id
        PLAN_STATE_MACHINES[plan_id] = sm

    transition = None
    if sm.current_state().value == "IDLE":
        transition = sm.trigger(
            "OBJECTIVE_INGRESS",
            actor=payload.actor,
            handshake_id=handshake_id,
        ).to_dict()

    handshake_bundle = build_handshake_bundle(
        db_manager=DBManager(),
        payload=payload,
        plan_id=plan_id,
        handshake_id=handshake_id,
        api_key_fingerprint=api_key_fingerprint,
    )
    state_payload = {
        "handshake_id": handshake_id,
        "plan_id": plan_id,
        "state_machine": sm.to_dict(),
        "transition": transition,
        **handshake_bundle,
    }

    return {
        "status": "handshake_initialized",
        "message": "Agents onboarded as stateful embedding artifacts.",
        "state_payload": state_payload,
    }


@app.post("/orchestrate")
async def orchestrate(user_query: str):
    """
    Triggers the full A2A pipeline (Managing->Orchestration->Architecture->Coder->Tester).
    Matches the contract expected by mcp_server.py.
    """
    engine = _get_engine()

    try:
        result = await engine.run_full_pipeline(
            description=user_query,
            requester="api_user",
        )

        return {
            "status": "A2A Workflow Complete",
            "success": result.success,
            "pipeline_results": {
                "plan_id": result.plan.plan_id,
                "blueprint_id": result.blueprint.plan_id,
                "code_artifacts": [a.artifact_id for a in result.code_artifacts],
            },
            "final_code": result.code_artifacts[-1].content if result.code_artifacts else None,
            "test_summary": (
                f"Passed: {sum(1 for v in result.test_verdicts if v['status'] == 'PASS')}"
                f"/{len(result.test_verdicts)}"
            ),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))



