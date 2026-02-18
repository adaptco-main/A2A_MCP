from fastapi import Body, FastAPI, HTTPException

from orchestrator import storage
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path

app = FastAPI(title="A2A MCP Orchestrator")

# In-memory cache of live state machines.
PLAN_STATE_MACHINES: dict[str, StateMachine] = {}


def _persistence_callback(plan_id: str | None, snapshot: dict) -> None:
    if not plan_id:
        return
    storage.save_plan_state(plan_id, snapshot)


def _load_or_create_machine(plan_id: str) -> StateMachine:
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


@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    """
    Accept either:
    - plan_id: canonical id
    - plan_file_path: path containing the plan id in basename
    """
    plan_id = payload.get("plan_id")
    if not plan_id:
        plan_file_path = payload.get("plan_file_path", "")
        plan_id = extract_plan_id_from_path(plan_file_path)

    if not plan_id:
        raise HTTPException(
            status_code=400,
            detail="Unable to determine plan_id; provide plan_id or plan_file_path",
        )

    plan_id = plan_id.strip()
    sm = _load_or_create_machine(plan_id)

    try:
        rec = sm.trigger("OBJECTIVE_INGRESS")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}


@app.post("/plans/{plan_id}/ingress")
async def plan_ingress_by_id(plan_id: str):
    plan_id = plan_id.strip()
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")

    sm = _load_or_create_machine(plan_id)

    try:
        rec = sm.trigger("OBJECTIVE_INGRESS")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": "scheduled", "plan_id": plan_id, "transition": rec.to_dict()}


@app.post("/plans/{plan_id}/dispatch")
async def dispatch_plan(plan_id: str):
    plan_id = plan_id.strip()
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")

    sm = _load_or_create_machine(plan_id)

    try:
        rec = sm.trigger("RUN_DISPATCHED")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {"status": "ok", "plan_id": plan_id, "transition": rec.to_dict()}


@app.get("/plans/{plan_id}/state")
async def get_plan_state(plan_id: str):
    plan_id = plan_id.strip()
    if not plan_id:
        raise HTTPException(status_code=400, detail="plan_id is required")

    sm = PLAN_STATE_MACHINES.get(plan_id)
    if sm:
        return {"plan_id": plan_id, "snapshot": sm.to_dict()}

    persisted_snapshot = storage.load_plan_state(plan_id)
    if not persisted_snapshot:
        raise HTTPException(status_code=404, detail="no plan")

    return {"plan_id": plan_id, "snapshot": persisted_snapshot}
