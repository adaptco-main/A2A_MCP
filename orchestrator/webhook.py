import os
import hashlib
import hmac
from typing import Optional

from fastapi import Body, FastAPI, Header, HTTPException, Request

from orchestrator import storage
from agents.cicd_monitor_agent import CICDMonitorAgent
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path

try:
    from orchestrator.verify_api import router as verify_router
except ImportError:
    verify_router = None

app = FastAPI(title="A2A MCP Webhook")
if verify_router:
    app.include_router(verify_router)

# In-memory stores. These can be backed by DB/Redis in production.
PLAN_STATE_MACHINES: dict[str, StateMachine] = {}
CI_CD_MONITOR = CICDMonitorAgent()
WEBHOOK_SHARED_SECRET = os.getenv("WEBHOOK_SHARED_SECRET", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


def _persistence_callback(plan_id: str | None, snapshot: dict) -> None:
    if not plan_id:
        return
    storage.save_plan_state(plan_id, snapshot)


def _resolve_plan_id(path_plan_id: str | None, payload: dict) -> str | None:
    if path_plan_id:
        return path_plan_id.strip()

    plan_id = payload.get("plan_id")
    if plan_id:
        return str(plan_id).strip()

    plan_file_path = payload.get("plan_file_path", "")
    extracted = extract_plan_id_from_path(plan_file_path)
    return extracted.strip() if extracted else None


def _extract_webhook_token(
    authorization: Optional[str],
    x_webhook_token: Optional[str],
) -> Optional[str]:
    if x_webhook_token:
        return x_webhook_token.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def _validate_webhook_token(
    authorization: Optional[str],
    x_webhook_token: Optional[str],
) -> None:
    # If secret isn't configured, webhooks are accepted (local/dev mode).
    if not WEBHOOK_SHARED_SECRET:
        return

    token = _extract_webhook_token(authorization, x_webhook_token)
    if token != WEBHOOK_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook token")


def _validate_github_signature(
    raw_body: bytes,
    signature_header: Optional[str],
) -> None:
    if not GITHUB_WEBHOOK_SECRET:
        return

    if not signature_header:
        raise HTTPException(status_code=401, detail="Missing GitHub webhook signature")
    if not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature format")

    supplied_digest = signature_header.split("=", 1)[1]
    expected_digest = hmac.new(
        key=GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(supplied_digest, expected_digest):
        raise HTTPException(status_code=401, detail="Invalid GitHub webhook signature")


def _get_or_create_state_machine(plan_id: str) -> StateMachine:
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if sm:
        return sm

    persisted_snapshot = storage.load_plan_state(plan_id)
    if persisted_snapshot:
        sm = StateMachine.from_dict(
            persisted_snapshot,
            persistence_callback=lambda pid, snap: _persistence_callback(pid, snap),
        )
    else:
        sm = StateMachine(
            max_retries=3,
            persistence_callback=lambda pid, snap: _persistence_callback(pid, snap),
        )

    sm.plan_id = plan_id
    PLAN_STATE_MACHINES[plan_id] = sm
    return sm


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

    sm = _get_or_create_state_machine(plan_id)
    rec = sm.trigger("OBJECTIVE_INGRESS")
    return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}


@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    return await _plan_ingress_impl(None, payload)


@app.post("/plans/{plan_id}/ingress")
async def plan_ingress_by_id(plan_id: str, payload: dict = Body(default={})):
    return await _plan_ingress_impl(plan_id, payload)


@app.post("/ingress")
async def ingress_compat(payload: dict = Body(...)):
    # Backward-compatible route for older workflows still calling /ingress.
    return await _plan_ingress_impl(None, payload)


@app.post("/plans/{plan_id}/dispatch")
async def dispatch_plan(plan_id: str):
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        raise HTTPException(status_code=404, detail="Unknown plan_id")

    rec = sm.trigger("RUN_DISPATCHED")
    return {"status": "ok", "plan_id": plan_id, "transition": rec.to_dict()}


@app.get("/plans/{plan_id}/state")
async def get_plan_state(plan_id: str):
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        raise HTTPException(status_code=404, detail="Unknown plan_id")

    return {"plan_id": plan_id, "snapshot": sm.to_dict()}


@app.post("/webhooks/github/actions")
async def ingest_github_actions_event(
    request: Request,
    payload: dict = Body(...),
    x_github_event: str = Header(default="workflow_run", alias="X-GitHub-Event"),
    x_webhook_token: Optional[str] = Header(default=None, alias="X-Webhook-Token"),
    x_hub_signature_256: Optional[str] = Header(default=None, alias="X-Hub-Signature-256"),
    authorization: Optional[str] = Header(default=None),
):
    raw_body = await request.body()
    if GITHUB_WEBHOOK_SECRET:
        _validate_github_signature(raw_body=raw_body, signature_header=x_hub_signature_256)
    else:
        _validate_webhook_token(authorization=authorization, x_webhook_token=x_webhook_token)

    try:
        snapshot = CI_CD_MONITOR.ingest_github_workflow_event(
            payload=payload,
            event_type=x_github_event,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "ok", "snapshot": snapshot}


@app.get("/cicd/status/{head_sha}")
async def get_cicd_status(head_sha: str):
    return CI_CD_MONITOR.get_commit_status(head_sha)


@app.get("/cicd/run/{run_id}")
async def get_cicd_run(run_id: int):
    run = CI_CD_MONITOR.get_run_status(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Unknown workflow run id")
    return run
