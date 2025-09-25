# Core Orchestrator

This repository coordinates automation and human operations around artifact management.

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

## Sovereign Wrapper Autocode (Queen CiCi)

Use the wrapper autocoder to verify that every vessel in the sovereign shell is stuck to the right runtime node before you
freeze or resume a flow. The script inspects `capsule.wrapper.adaptco_os.v1`, checks that Queen CiCi is still the stabilizer,
and confirms that each anchor in the expanded braid is bound inside the runtime registry.

```bash
./scripts/autocode_wrapper.js
```

Pass `--compact` for single-line JSON or override the wrapper/registry locations via `--wrapper`, `--registry`, and
`--runtime-dir` when running against alternate checkouts. The report includes sticky counts so CiCi can spot any anchors that
are still rehearsing before the council seals the shell.

