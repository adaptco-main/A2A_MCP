# Core Orchestrator

The Core Orchestrator keeps changes landing on `main` predictable, auditable, and fast to recover from. Operators and automation
share the same merge automation so every branch headed toward production is fetched, validated, and merged with the same guardrail
set.

## Core Merge Orchestrator Agent

`app/orchestrator_agent.py` provides the `CoreOrchestratorMergeAgent`, the main automation entrypoint for harvesting remote
branches, rehearsing merges, and committing successful integrations.

### Capabilities
- **Remote coordination** – fetch and prune the configured remote, fast-forward the base branch, and push results.
- **Merge planning** – build deterministic merge queues with `plan_merges()` using include/exclude patterns that match remote
  and branch suffixes.
- **Dry-run rehearsals** – simulate merges with `dry_run=True` to surface conflicts without touching the working tree.
- **Sequential execution** – `merge_all()` processes a queue of branches, halting on the first failure so operators can inspect
  the audit trail before continuing.
- **Failure visibility** – captured stdout/stderr for failing commands are returned in the `MergeResult` payload for quick
  troubleshooting and `exit code 128` style errors.

### Quick start
```python
from pathlib import Path

from app.orchestrator_agent import CoreOrchestratorMergeAgent

workspace = Path("/workspace/core-orchestrator")
agent = CoreOrchestratorMergeAgent(workspace)
agent.configure_identity(name="Merge Bot", email="merge@example.com")

# Stay in sync with origin/main before merging new branches
agent.fetch_remote()
agent.pull_base()

plan = agent.plan_merges(include_patterns=("feature/*",), exclude_patterns=("feature/wip/*",))
results = agent.merge_all(plan)
for result in results:
    print(result.branch, result.success, result.commit)
```

### Dry run and conflict handling
```python
dry_run = agent.merge_branch("origin/feature/landing", dry_run=True)
if dry_run.success:
    print("Merge is clean")
else:
    print("Needs attention:", dry_run.message)

# Execute the real merge once the branch is ready
result = agent.merge_branch("origin/feature/landing")
if not result.success:
    print(result.message)
    print(result.details.get("stderr"))
```

### Merge plan automation
`plan_merges()` returns `MergeCommand` items that include the branch ref, commit SHA, and subject line. Feed them directly into
`merge_all()` to merge them in commit-date order. The agent will stop at the first failure and leave the working tree clean by
aborting partially applied merges.

```python
plan = agent.plan_merges(include_patterns=("feature/*",), exclude_patterns=("feature/wip/*",))
results = agent.merge_all(plan, dry_run=False, fast_forward=False)
for report in results:
    if report.success:
        print(f"Merged {report.branch} -> {report.commit}")
    else:
        print(f"Stopped on {report.branch}: {report.message}")
        break
```

## Repository Components
- `app/orchestrator_agent.py` — Core merge agent used by automation and operators to pull, rehearse, and merge inbound branches.
- `capsules/orchestrator/core/capsule.orchestrator.core.celine.v7.json` — Governance capsule delegating repository lifecycle
  authority from CiCi to Celine with maker-checker enforcement.
- `docs/celine_orchestrator_handoff.md` — Operational logic tree and integration guardrails for activating the Celine capsule.
- `docs/mission_oversight_widgets.md` — Human-readable widget catalog and guardrail summary for the live mission HUD.
- `specs/mission.oversight.hud.contract.v1.json` — Contract describing the HUD data streams, layout, and fail-closed alert wiring.
- `specs/mission.meta.directive.v1.schema.json` — Protocol schema encoding the mission state machine, retarget logic, and rollback
  rules.
- `specs/fixtures/mission.solstice.directive.json` — Solstice Dawn directive fixture illustrating the schema in practice.

## Mission Oversight Foundations
- `specs/mission.oversight.hud.contract.v1.json` — Contract describing the data streams, widgets, and alerting that power the live
  mission HUD.
- `docs/mission_oversight_widgets.md` — Human-readable widget catalog and guardrail summary.
- `specs/mission.meta.directive.v1.schema.json` — Protocol schema that encodes the mission state machine, retarget, and rollback
  rules.
- `specs/fixtures/mission.solstice.directive.json` — Sample directive fixture seeded for the Solstice Dawn mission.

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

## Governance Principles
- **SSOT Enforcement**: All artifacts hash-verified
- **Audit-First**: Every action logged with timestamp, actor, and hash
- **Rollback Ready**: Every deploy has a tested rollback path
- **Operator in the Loop**: No hidden automation

## Getting Started
1. Clone repo and configure `.env` with GitHub token for dispatch events.
2. Run the merge agent from automation or locally to integrate feature branches into `main`.
3. Deploy cockpit overlay JSON to your Live Ops UI.
4. Connect GitHub webhooks to cockpit event listener.
5. Test with a Freeze Artifact quick-action.
