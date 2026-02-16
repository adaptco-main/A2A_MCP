<<<<<<< ours
# inside A2A_MCP/orchestrator/webhook.py
from fastapi import FastAPI, HTTPException, Body
from orchestrator.stateflow import StateMachine
from orchestrator.utils import extract_plan_id_from_path
=======
from fastapi import FastAPI, HTTPException, BackgroundTasks
from orchestrator.stateflow import StateMachine, State
from orchestrator.intent_engine import IntentEngine
from orchestrator.scheduler import SimpleScheduler
from orchestrator import storage
>>>>>>> theirs

app = FastAPI(...)

<<<<<<< ours
# in-memory map (replace with DB-backed persistence or plan state store in prod)
=======
# in-memory cache of live state machines
>>>>>>> theirs
PLAN_STATE_MACHINES = {}

<<<<<<< ours
@app.post("/plans/ingress")
async def plan_ingress(payload: dict = Body(...)):
    """
    Accepts:
      - plan_id: optional canonical id
      - plan_file_path: optional file path that contains plan id in its basename
    Prioritizes plan_id if given; otherwise tries to extract id from plan_file_path.
    """
    plan_id = payload.get("plan_id")
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
@app.post("/plans/{plan_id}/ingress")
async def plan_ingress(plan_id: str, background: BackgroundTasks):
    # Create or fetch persisted state machine snapshot
    persisted_snapshot = storage.load_plan_state(plan_id)
    if persisted_snapshot:
        sm = StateMachine.from_dict(
            persisted_snapshot,
            persistence_callback=lambda pid, snap: storage.save_plan_state(pid, snap),
        )
    else:
        sm = StateMachine(
            max_retries=3,
            persistence_callback=lambda pid, snap: storage.save_plan_state(pid, snap),
        )
    sm.plan_id = plan_id

    # register callback: when executing, run the intent engine
    def on_executing(rec):
        # run IntentEngine asynchronously
        async def run_engine():
            try:
                await engine.process_plan(plan)  # plan must be loaded or passed in
                # after engine finishes: trigger completion
                sm.trigger("EXECUTION_COMPLETE", artifact_id="...") 
            except Exception as exc:
                # on error trigger repair
                sm.trigger("EXECUTION_ERROR", details=str(exc))
        import asyncio
        asyncio.create_task(run_engine())

    sm.register_callback(State.EXECUTING, on_executing)
    # persist mapping
    PLAN_STATE_MACHINES[plan_id] = sm
    rec = sm.trigger("OBJECTIVE_INGRESS")
    return {"status":"ok","transition":rec.__dict__}

@app.post("/plans/{plan_id}/dispatch")
async def dispatch_plan(plan_id: str):
    sm = PLAN_STATE_MACHINES.get(plan_id)
    if not sm:
        persisted_snapshot = storage.load_plan_state(plan_id)
        if not persisted_snapshot:
            raise HTTPException(404, "no plan")
        sm = StateMachine.from_dict(
            persisted_snapshot,
            persistence_callback=lambda pid, snap: storage.save_plan_state(pid, snap),
        )
        sm.plan_id = plan_id
        PLAN_STATE_MACHINES[plan_id] = sm
    rec = sm.trigger("RUN_DISPATCHED")
    return {"status":"ok","transition":rec.__dict__}
>>>>>>> theirs
