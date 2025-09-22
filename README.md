# Core Orchestrator

The Core Orchestrator aligns human operators and automation so that artifact changes land on `main` with traceable intent and full mission context. This repository houses the merge automation, mission oversight contracts, and the governance scaffolding that keeps the system auditable.

## Qube Workflow Orchestration

The Qube mission roadmap advances through deliberate, auditable workflow steps. The **Qube Workflow Agent** is the main agent model responsible for sequencing those steps, enforcing dependencies, and maintaining a ledger of every transition.

### 1. Load the roadmap
Roadmaps can be sourced from YAML (install `pyyaml`) or from an in-memory payload. Example loading from the execution roadmap:

```python
from app.orchestrator_agent import QubeWorkflowAgent

# YAML support requires `pip install pyyaml`
agent = QubeWorkflowAgent.from_dict({
    "name": "Qube Integration",
    "tasks": [
        {"id": "phase0.authority_map_cutover", "title": "Authority Map Cutover"},
        {"id": "phase0.capsule_remap_freeze", "title": "Capsule Remap Freeze", "depends_on": ["phase0.authority_map_cutover"]},
    ],
})
```

### 2. Inspect what is ready
Call `ready_tasks()` to identify the next actionable work. Tasks return in dependency order to keep the mission synchronized.

```python
for task in agent.ready_tasks():
    print(task.id, task.title)
```

### 3. Drive the workflow
Transitions must honor dependencies. Each call records an event that can be replayed for audit or streamed into HUD surfaces.

```python
agent.start_task("phase0.authority_map_cutover", actor="ops", assignee="Maker")
agent.complete_task(
    "phase0.authority_map_cutover",
    actor="ops",
    deliverables=("authority_map.vN.canonical.json", "authority_map.vN.sig"),
)

agent.start_task("phase0.capsule_remap_freeze", actor="ops")
```

### 4. Monitor status
Dashboards can consume `status_summary()` or the structured payload from `serialize_state()` to surface counts, ready work, and the audit log.

```python
summary = agent.status_summary()
print(summary["counts"])
print(summary["ready"])
```

### 5. Handle exceptions deliberately
- Use `block_task()` when external issues stall progress.
- Call `unblock_task()` to return the task to the pending queue once the blocker clears.
- Apply `reset_task()` with a reason to rewind work that needs re-verification.

Every transition produces a timestamped `WorkflowEvent`. Feed these into ledger writers or mission HUD annotations so operators see the same ground truth that automation enforces.

## Repository Components
- `app/orchestrator_agent.py` — Main workflow agent that sequences Qube roadmap tasks and records the audit log.
- `docs/mission_oversight_widgets.md` — Human-readable widget catalog and guardrail summary for the live mission HUD.
- `specs/mission.oversight.hud.contract.v1.json` — Contract describing the HUD data streams, layout, and fail-closed alert wiring.
- `specs/mission.meta.directive.v1.schema.json` — Protocol schema encoding the mission state machine, retarget logic, and rollback rules.
- `specs/fixtures/mission.solstice.directive.json` — Solstice Dawn directive fixture illustrating the schema in practice.

## Control Surfaces (Human-Operated)
- **Quick-Action Panel**: Freeze, Override, Flag
- **Workflow Ledger Viewer**: Inspect all actions
- **Preview + Render Controls**: Trigger visual outputs
- **Mind Map + State Tracker**: Visualize live state and transitions
- **Help Bubbles**: Contextual guidance

## Automated Surfaces (Agent-Operated)
- **GitHub Actions**: Validate, freeze, override, drift check, ledger sync
- **Codex Scripts**: Parse manifests, enforce rules, generate previews
- **Ledger Writers**: Auto-log every action
- **Drift Detectors**: Compare SSOT vs deployed artifacts
- **Rollback Validators**: Check readiness and compliance

## Agent Models

- **Qube Workflow Agent** — Main automation entrypoint that sequences roadmap tasks, enforces dependency ordering, and logs every transition for audit and HUD consumption.

### Qube Workflow Agent

The workflow agent lives in `app/orchestrator_agent.py` and exposes an intentionally small control surface:
1. Instantiate from a roadmap definition (`from_dict` or `from_yaml`).
2. Call `ready_tasks()` to understand the next safe operation.
3. Drive progress with `start_task`, `complete_task`, `block_task`, `unblock_task`, and `reset_task`.
4. Consume `history()` and `serialize_state()` for ledger sync, HUD rendering, or council reviews.

## Mission Oversight Foundations
- `specs/mission.oversight.hud.contract.v1.json` — Contract describing the data streams, widgets, and alerting that power the live mission HUD.
- `docs/mission_oversight_widgets.md` — Human-readable widget catalog and guardrail summary.
- `specs/mission.meta.directive.v1.schema.json` — Protocol schema that encodes the mission state machine, retarget, and rollback rules.
- `specs/fixtures/mission.solstice.directive.json` — Sample directive fixture seeded for the Solstice Dawn mission.

## How It Works
1. Operator triggers an action in the cockpit (e.g., Freeze Artifact).
2. Cockpit dispatches a GitHub event with payload (artifact ID, notes).
3. GitHub Action runs the corresponding script (e.g., `freeze.py`).
4. Script updates the artifact state, validates against SSOT, logs to ledger.
5. Cockpit updates in real time via ledger feed + state tracker.

## Governance Principles
- **SSOT Enforcement**: All artifacts hash-verified
- **Audit-First**: Every action logged with timestamp, actor, and hash
- **Rollback Ready**: Every deploy has a tested rollback path
- **Operator in the Loop**: No hidden automation

## Getting Started
1. Clone repo and configure `.env` with GitHub token for dispatch events.
2. Deploy cockpit overlay JSON to your Live Ops UI.
3. Connect GitHub webhooks to cockpit event listener.
4. Test with a Freeze Artifact quick-action.

