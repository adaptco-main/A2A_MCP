# core-orchestrator

This repository collects a variety of utilities, scripts, and service prototypes that
support the Adapt/Co core orchestrator. The latest addition is a cryptographic ledger
verification tool that ensures append-only event ledgers have not been tampered with.

## Ledger verification utility

Use `scripts/verify-ledger.js` to validate that a ledger's hash chain and digital
signatures match the expected values. The tool accepts standard JSON array ledgers as
well as newline-delimited JSON (`.jsonl`) ledgers.

### Usage

```bash
npm run verify:ledger -- --ledger path/to/ledger.json --pub-key path/to/public.pem
```

The command exits with code `0` when all entries validate and `1` otherwise.

### Tests

Run the accompanying Node.js tests to confirm the verifier's behaviour:

```bash
npm run test:ledger
```

The tests cover hash calculation, signature checking, JSON Lines parsing, and error
reporting for malformed ledgers.
# Core Orchestrator

The Core Orchestrator repo keeps the `selector.preview.bundle.v1` rehearsal space aligned
across manifests, automation, and operator tooling. It documents how the rehearsal
prompts, governance workflows, and ledgers interact so pull requests can be merged and
the preview bundle can be generated on demand.

## Repository layout

```
.github/workflows/
  governance_check.yml   # CI validation for manifests and ledgers
  freeze_artifact.yml    # Manual snapshot of manifests for later playback
  override_request.yml   # Manual governance override logging
  ledger_sync.yml        # Hourly digest of ledger events
scripts/
  validate_ssot.py       # Strict validation of the SSOT manifest
  check_drift.py         # Drift detection between SSOT and deployed manifests
  freeze.py              # Utility for freezing manifest snapshots
  generate_preview.sh    # Local rehearsal helper for preview prompts
  log_action.py          # Ledger and audit-trail logger/validator
manifests/
  ssot.yaml              # Declared state for selector.preview.bundle.v1
  deployed.yaml          # Most recent deployed view of the bundle
  artifacts/
    abc123.yaml          # Historical manifest snapshot
    def456.yaml          # Historical manifest snapshot
ledger/
  workflow_ledger.json   # JSON append-only log of workflow events
  audit_trail.csv        # CSV mirror of ledger entries
cockpit/
  ui_overlay.json        # HUD overlay definition for preview cockpit
  quick_actions.json     # Quick action triggers for operators
```

## Working with manifests

1. Edit `manifests/ssot.yaml` to adjust the rehearsal modules or metadata.
2. Update `manifests/deployed.yaml` when the live environment catches up.
3. Run the validation scripts locally before opening a pull request:

   ```bash
   python -m pip install --upgrade pip pyyaml
   python scripts/validate_ssot.py
   python scripts/check_drift.py
   ```

   The drift check will exit non-zero if a module or version mismatch is detected. Fix
the manifests until the check passes to keep governance noise low.

## Creating manifest snapshots

Use the freeze utility to capture the current SSOT manifest into the `artifacts/`
folder. Provide a descriptive tag so it is easy to locate later.

```bash
python scripts/freeze.py --tag rehearsal-2024-06-01
```

Each snapshot is a verbatim copy of the SSOT manifest, making it trivial to diff against
future states.

## Logging governance activity

All automated and manual events should flow into the ledger so the system maintains an
agentic audit trail. Append new entries with `log_action.py`:

```bash
python scripts/log_action.py --event override --ticket OVERRIDE-42 \
  --message "Temporarily disabling compliance overlay"
```

Use `--check-only` to ensure the ledger and audit trail are formatted correctly during CI
runs, and `--summarize` to render a quick breakdown of event counts.

## Preview rehearsal loop

The `scripts/generate_preview.sh` helper validates the manifests and echoes the active
rehearsal prompts so creative teams can spin up the experience locally. The prompts match
the rehearsal modules:

- `rupture.flare` → irony shimmer + spark trace
- `restoration.loop` → breath sync + glyph fidelity
- `mesh.response` → empathy shimmer + echo match

Integrate the output with your renderer of choice to produce the requested video or
interactive preview.

## Automation overview

- **Governance Check** ensures every pull request keeps manifests and ledgers healthy.
- **Freeze Artifact** allows maintainers to capture immutable manifest snapshots on
  demand.
- **Override Request** records manual interventions directly into the ledger.
- **Ledger Sync** posts hourly summaries via the GitHub Actions step summary so
  stakeholders can monitor activity without digging through raw files.

Keep the README updated as workflows evolve so downstream agents and operators can follow
the same process without guesswork.
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

## P3L Semantics (Proof → Flow → Execution)
- **Proof**: Seals data to guarantee integrity and immutability using cryptographic hashing, Merkle tree anchoring, and council attestations.
- **Flow**: Routes and governs operations through defined avatars, enforcing policies like `no_drift` and `quorum_check` so actions stay aligned with approved roles.
- **Execution**: Manifests creative outputs by generating frame-accurate motion ledgers, assembling 5–10 second clips, and returning resulting fossils to the Single Source of Truth (SSOT).

## Getting Started
1. Clone repo and configure `.env` with GitHub token for dispatch events.
2. Deploy cockpit overlay JSON to your Live Ops UI.
3. Connect GitHub webhooks to cockpit event listener.
4. Test with a Freeze Artifact quick-action.

## Capsule Preview Utility
- Run `npm run preview` to list the staged capsules along with their type, version, and attestation status.
- Pass a capsule id or filename (for example `npm run preview -- capsule.broadcast.worldengine.v1`)
  to inspect the detailed payload, routing, and governance metadata for a specific artifact.

## Mock Telemetry Server
- Run `npm install` to ensure dependencies are available.
- Start the simulated HUD stream with `npm run start:mock-telemetry`.
- Connect a WebSocket client to `ws://localhost:8080/streams/telemetry/solF1/v1` using token `demo` (either query string `?token=demo` or `Authorization: Bearer demo`).
- The server replays `capsules/telemetry/capsule.telemetry.render.v1.events_examples.jsonl` at 30Hz in a loop and exposes a `/healthz` endpoint for status checks.
- Validate fixture integrity with `npm run validate:telemetry` (supports overriding the fixture path via CLI arg or `TELEMETRY_EVENT_FILE`).

## Scrollstream Rehearsal Loop
- Stage the rehearsal capsule ledger entries with `npm run stage:rehearsal`.
- Pass `--training` to emit deterministic timestamps for CI/CD smoke tests (or set `REHEARSAL_TRAINING=1`).
- Override the ledger destination with `--ledger <path>` if you need to append to a non-default scrollstream ledger.

## Contributor Echo Trace
- Generate an echo trace ledger that mirrors the active avatar bindings with `npm run inscribe:echo`.
- Pass `--seed <iso8601>` for deterministic timestamps or `--mode overwrite` to rebuild the ledger from scratch.
- Use `--dry-run` to preview the contributor table without writing to disk.

## Glyphstream Overlay Preview
- Produce a glyphstream overlay scaffold for apprentice ignition arcs with `npm run preview:glyphstream`.
- Combine with `--pretty` for human-readable JSON or `--dry-run` to limit the command to console output.
- Provide an alternate avatar dataset via `--source` when evaluating experimental bindings.

