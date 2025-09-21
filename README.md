# Core Orchestrator

The Core Orchestrator aligns human operators and automation so that artifact changes land on `main` with traceable intent and full mission context. This repository houses the merge automation, mission oversight contracts, and the governance scaffolding that keeps the system auditable.

## Main Branch Merge Workflow

The `main` branch is the reproducible source of truth. Use the Core Orchestrator merge agent to stage, verify, and publish updates.

### 1. Prepare the workspace
- Clone the repository and ensure your Git remote is set to the canonical origin.
- Install Python 3.10+ and make sure the `jsonschema` dependency is available for schema validation.
- Confirm your worktree is clean (`git status --short` should return no entries).

### 2. Run the required checks
All merges to `main` must be accompanied by a clean test run and schema validation:

```bash
python -m unittest discover -s tests -p 'test_*.py'
python - <<'PY'
import json
from pathlib import Path
from jsonschema import Draft7Validator

schema = json.loads(Path('specs/mission.meta.directive.v1.schema.json').read_text())
validator = Draft7Validator(schema)
instance = json.loads(Path('specs/fixtures/mission.solstice.directive.json').read_text())
validator.validate(instance)
PY
```

### 3. Plan the merge
Run the merge agent in dry-run mode to understand which branches will land on `main`:

```python
from app.orchestrator_agent import CoreOrchestratorMergeAgent

agent = CoreOrchestratorMergeAgent('path/to/core-orchestrator')
report = agent.pull_and_merge(
    target_branch='main',
    include_prefixes=('feature/', 'hotfix/', 'chore/'),
    dry_run=True,
)

for outcome in report.outcomes:
    print(outcome.branch, outcome.skipped_reason)
```

Branches listed with `dry-run` are ready to merge once the plan looks correct.

### 4. Merge and push
Execute the real merge once the dry run looks good. The agent enforces a clean worktree, performs sequential merges, and can publish the result back to the remote:

```python
report = agent.pull_and_merge(
    target_branch='main',
    include_prefixes=('feature/', 'hotfix/', 'chore/'),
    push_after_merge=True,
)

for outcome in report.outcomes:
    status = 'merged' if outcome.merged else outcome.skipped_reason or 'skipped'
    print(f"{outcome.branch}: {status}")
```

If a branch fails to merge, the agent records the error and either aborts or continues based on `stop_on_failure`.

### 5. Post-merge verification
- Review the command transcript in `report.setup_commands` and each `MergeOutcome.commands` entry.
- `git status` should remain clean. If `push_after_merge=False`, push the branch manually once verified.
- Announce the successful merge in the workflow ledger and update any mission directives that rely on the new state.

### Troubleshooting
- **Dirty worktree**: Commit or stash your changes before running the agent; it refuses to operate with pending edits.
- **Blocked branches**: Outcomes flagged with `blocked-by-failure` indicate downstream branches that were skipped after an earlier conflict; resolve the conflict and re-run the merge.
- **Remote drift**: Rerun `pull_and_merge` to incorporate new inbound branches. The agent always fetches before planning.

## Repository Components
- `app/orchestrator_agent.py` — Merge automation for converging feature branches onto `main`.
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

- **Core Orchestrator Merge Agent** — Git-native automation that pulls inbound branches, merges them into a designated target branch, and optionally pushes the results.

### Core Orchestrator Merge Agent

The merge agent lives in `app/orchestrator_agent.py` and wraps Git operations with guardrails:
1. Ensures the repository exists and the worktree is clean before doing anything.
2. Fetches and filters remote branches by prefix, explicit allow/deny rules, or both.
3. Sequentially merges each eligible branch into the target and can push after every success.

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

