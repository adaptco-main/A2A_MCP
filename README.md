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

## Mock Telemetry Server
- Run `npm install` to ensure dependencies are available.
- Start the simulated HUD stream with `npm run start:mock-telemetry`.
- Connect a WebSocket client to `ws://localhost:8080/streams/telemetry/solF1/v1` using token `demo` (either query string `?token=demo` or `Authorization: Bearer demo`).
- The server replays `capsules/telemetry/capsule.telemetry.render.v1.events_examples.jsonl` at 30Hz in a loop and exposes a `/healthz` endpoint for status checks.
- Validate fixture integrity with `npm run validate:telemetry` (supports overriding the fixture path via CLI arg or `TELEMETRY_EVENT_FILE`).

