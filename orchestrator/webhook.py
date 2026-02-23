import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import BackgroundTasks, Body, FastAPI, Header, HTTPException, Request

from agents.cicd_monitor_agent import CICDMonitorAgent
from orchestrator import storage
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path

try:
    from orchestrator.verify_api import router as verify_router
except ImportError:
    verify_router = None

if TYPE_CHECKING:
    from orchestrator.intent_engine import IntentEngine

app = FastAPI(title="A2A MCP Webhook")
if verify_router:
    app.include_router(verify_router)

# In-memory stores. These can be backed by DB/Redis in production.
PLAN_STATE_MACHINES: dict[str, StateMachine] = {}
RELEASE_JOBS: Dict[str, Dict[str, Any]] = {}
CI_CD_MONITOR = CICDMonitorAgent()
WEBHOOK_SHARED_SECRET = os.getenv("WEBHOOK_SHARED_SECRET", "")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
_engine: Optional["IntentEngine"] = None


def _get_engine() -> "IntentEngine":
    global _engine
    if _engine is None:
        from orchestrator.intent_engine import IntentEngine

        _engine = IntentEngine()
    return _engine


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
    sm = _get_or_create_state_machine(plan_id)
    rec = sm.trigger("RUN_DISPATCHED")
    return {"status": "ok", "plan_id": plan_id, "transition": rec.to_dict()}


@app.get("/plans/{plan_id}/state")
async def get_plan_state(plan_id: str):
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if sm:
        return {"plan_id": plan_id, "snapshot": sm.to_dict()}

    persisted_snapshot = storage.load_plan_state(plan_id)
    if not persisted_snapshot:
        raise HTTPException(status_code=404, detail="no plan")

    return {"plan_id": plan_id, "snapshot": persisted_snapshot}


@app.post("/webhooks/release")
async def release_webhook(
    payload: dict = Body(...),
    background: BackgroundTasks = None,
    x_webhook_token: Optional[str] = Header(default=None, alias="X-Webhook-Token"),
    x_webhook_provider: Optional[str] = Header(default="generic", alias="X-Webhook-Provider"),
    x_webhook_event: Optional[str] = Header(default="release", alias="X-Webhook-Event"),
):
    _validate_webhook_token(authorization=None, x_webhook_token=x_webhook_token)

    release_id = str(uuid.uuid4())
    RELEASE_JOBS[release_id] = {
        "release_id": release_id,
        "status": "accepted",
        "provider": x_webhook_provider or "generic",
        "event_type": x_webhook_event or "release",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None,
    }

    async def _run_job() -> None:
        RELEASE_JOBS[release_id]["status"] = "running"
        RELEASE_JOBS[release_id]["started_at"] = datetime.now(timezone.utc).isoformat()
        try:
            result = await _get_engine().run_release_workflow_from_webhook(
                payload=payload,
                provider=x_webhook_provider or "generic",
                event_type=x_webhook_event or "release",
            )
            RELEASE_JOBS[release_id]["status"] = "completed"
            RELEASE_JOBS[release_id]["result"] = result
            RELEASE_JOBS[release_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            RELEASE_JOBS[release_id]["status"] = "failed"
            RELEASE_JOBS[release_id]["error"] = str(exc)
            RELEASE_JOBS[release_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    if background is None:
        # Log a warning or raise an error if background tasks are expected but not provided
        # For now, we'll just run it directly, but this might block the request.
        self.logger.warning("BackgroundTasks not provided, running release job synchronously.")
        await _run_job()
    else:
        background.add_task(_run_job)

    return {"status": "accepted", "release_id": release_id}


@app.get("/webhooks/release/{release_id}")
async def get_release_status(release_id: str):
    job = RELEASE_JOBS.get(release_id)
    if not job:
        raise HTTPException(status_code=404, detail="release job not found")
    return job


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