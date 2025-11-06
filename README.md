# Core Orchestrator Governance Pilot

> **Developer note.**
> * Signing is performed with [`cosign sign-blob`](https://github.com/sigstore/cosign). For development you can supply `SIGNER=/path/to/mock_cosign` when running the freeze or pilot scripts.
> * Ledger interactions default to `http://localhost:3000`. Export `LEDGER_BASE_URL` to point at a real registry when wiring into production infrastructure.
> * Hardware-backed signing and long-term ledger persistence are not implemented. The in-memory ledger client in `server/index.js` is a drop-in seam for real HSM and registry integrations.

## Repository layout

| Path | Purpose |
| --- | --- |
| `capsules/` | Council and rehearsal capsules that define quorum and scrollstream lifecycles. |
| `governance/` | Canonical authority map and capsule remap manifests. |
| `lib/` | Manifest bindings adapter (`bindings.js`) and QBus gate middleware (`qbusGates.js`). |
| `public/hud/` | Heads-up display assets (`badges.js`) for policy verification badges. |
| `scripts/` | Freeze scripts for governance manifests. |
| `server/` | Minimal Express server that wires manifests, HUD state, and QBus enforcement. |
| `tests/` | Bash + Node based regression tests and signing fixtures. |

## Prerequisites

* Node.js 18+
* `npm`, `jq`, `curl`, and `sha256sum`
* [`cosign`](https://github.com/sigstore/cosign) **or** a compatible signer exposed via the `SIGNER` environment variable for development/testing

Install Node dependencies once:

```bash
npm install
```

## Governance freeze scripts

Freeze scripts produce a canonical JSON, a SHA256 hash, and a cosign signature for each manifest. Cosign must be available or delegated through `SIGNER`.

```bash
# Freeze both manifests
scripts/freeze_authority_map.sh
scripts/freeze_remap.sh
```

Outputs will appear alongside the source manifests as `*.canonical.json`, `*.hash`, and `*.sig`. Remove them when no longer needed.

## QBus gate and bindings tests

Two bash entry points exercise the freeze scripts and the QBus middleware. Both print explicit PASS/FAIL lines.

```bash
# Run freeze script tests (uses an inline cosign stub)
npm run test:freeze

# Run QBus gate tests (Node-based harness)
npm run test:qbus

# Run both
npm test
```

Example excerpt:

```
PASS: authority_map canonical generated
PASS: freeze_authority_map.sh emits cosign guidance
PASS: G1 allows authorized binding (also G2 positive)
PASS: G3 blocks manifest that is not yet effective
```

## Running the Express server

Start the server (defaults to `PORT=3000`):

```bash
npm start
```

Key endpoints:

* `GET /health` &mdash; manifest hash, duo signature status, and recent gate events.
* `GET /hud/state.json` &mdash; cached HUD payload generated via `lib/bindings.buildHudState`.
* `GET /qbit/proof.latest.v1` &mdash; latest proof and policy tag for the HUD badge client.
* `POST /ledger/freeze` &mdash; accept freeze artifacts (`name`, `hash`, `signature`, `canonical`).
* `GET /ledger/snapshot` &mdash; snapshot combining latest proof and stored freeze artifacts.
* `POST /scrollstream/rehearsal` &mdash; emit the deterministic Celine → Luma → Dot rehearsal loop into the scrollstream ledger.
* `GET /scrollstream/ledger` &mdash; inspect the replayable scrollstream ledger events captured by rehearsal cycles.
* `POST /capsule/execute` &mdash; protected endpoint enforced by QBus gates.

Sample health check:

```bash
curl -s http://localhost:3000/health | jq
```

```
{
  "status": "ok",
  "manifest": {
    "hash": "…",
    "hash_matches": true,
    "duo": { "ok": true, "maker": { "verified": true }, "checker": { "verified": true } }
  },
  "ledger": { "recent_events": [] }
}
```

Static HUD assets are served from `/public`. Include `public/hud/badges.js` in any page to render live badges sourced from `/qbit/proof.latest.v1`.

### Scrollstream rehearsal loop

Stage the rehearsal loop to populate the `scrollstream_ledger` with the deterministic Celine → Luma → Dot cycle:

```bash
curl -s -X POST http://localhost:3000/scrollstream/rehearsal | jq '.events[0]' 
```

Example response excerpt:

```json
{
  "capsule_id": "capsule.rehearsal.scrollstream.v1",
  "cycle_id": "cycle-2024-03-11T12:00:00.000Z",
  "stage": "audit.summary",
  "agent": { "name": "Celine", "role": "Architect" },
  "output": "Celine threads the capsule brief into the braid summary.",
  "emotive": ["irony shimmer", "spark trace"],
  "glyph": "hud.shimmer",
  "timestamp": "2024-03-11T12:00:00.000Z"
}
```

Fetch the ledger to confirm the shimmer trail:

```bash
curl -s http://localhost:3000/scrollstream/ledger | jq '.ledger | length'
```

## Pilot workflow runner

`run_pilot_workflow.sh` orchestrates the freeze, ledger publication, and snapshot validation flow. Requirements:

1. The Express server must be running (defaults to `http://localhost:3000`).
2. Cosign must be available (`cosign` in `$PATH`) or exported via `SIGNER`.

Run the pilot:

```bash
# Example using a mock signer
export SIGNER="$(pwd)/tests/mock_cosign.sh"   # provide your signer command
./run_pilot_workflow.sh
```

Expected output (truncated):

```
[pilot] Freezing authority map
[pilot] Publishing freeze artifact for authority_map.v1
[pilot] Ledger acknowledged authority_map.v1 with hash …
[pilot] Pilot workflow complete. Ledger snapshot is consistent with local freeze artifacts.
```

Override the target ledger with `LEDGER_BASE_URL=https://ledger.example.com ./run_pilot_workflow.sh` when integrating with a real registry.

## HUD badge client

`public/hud/badges.js` fetches `/qbit/proof.latest.v1` at a regular cadence, renders hash/duo/policy badges, and exposes “Refresh” and “Rehash” controls. Network errors emit a single warning per message and display an offline badge. The rehash button refetches the proof and recomputes a SHA-256 hash against `/governance/authority_map.v1.canonical.json`.

Include it in any page:

```html
<script src="/hud/badges.js" defer></script>
<div id="hud-badge-root"></div>
```

A running server is required for live data.

## Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `PORT` | Express server port | `3000` |
| `HUD_POLICY_TAG` | Policy label included in proofs | `pilot-alpha` |
| `QBUS_SKEW_SECONDS` | Time skew tolerance for G3 checks | `30` |
| `LEDGER_BASE_URL` | Base URL used by `run_pilot_workflow.sh` | `http://localhost:3000` |
| `SEAL_ROOT_SCRIPT` | Override path to the auto-seal script | `ops/v7_seal_root.sh` |
| `SIGNER` | Override signer command used by freeze scripts | *(unset)* |

### Automatic Merkle sealing

Whenever new freeze artifacts are published the in-memory ledger computes a Merkle
root across the stored artifacts and invokes `ops/v7_seal_root.sh` (or the path
configured via `SEAL_ROOT_SCRIPT`). The script receives the Merkle root as its
first argument and the complete payload in the `MERKLE_PAYLOAD` environment
variable, enabling external council or HSM processes to observe and sign new
roots without manual ceremony.

## Next steps

* Swap the in-memory ledger client for persistent storage with audit history.
* Wire `ledgerClient.storeFreezeArtifact` to a real registry API.
* Replace the cosign development stub with production signing keys or an HSM-backed signer.
# Task Middleware

FastAPI service to synchronize tasks between Monday.com and Airtable with
verification gates.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e .[development]
cp .env.example .env
```

## Development

Run tests and linters:

```bash
pytest
```

Start server:

```bash
uvicorn app.main:app --reload
```
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

## Governance Principles
- **SSOT Enforcement**: All artifacts hash-verified
- **Audit-First**: Every action logged with timestamp, actor, and hash
- **Rollback Ready**: Every deploy has a tested rollback path
- **Operator in the Loop**: No hidden automation

## P3L Semantics (Proof → Flow → Execution)

### ZERO_DRIFT Assertions
1. **Kinematic lock** — The stage and seal ledger events must carry a `ZERO_DRIFT` gate outcome that affirms the avatar choreography stayed aligned with the reference fossil. The rehearsal ledger captures the raw motion deltas and the seal step repeats the check with the final artifact hash so both the pre-seal and post-seal records agree on drift-free motion.
2. **Council quorum** — The `capsule.sealed` entry requires the 2-of-3 attestation quorum defined in the export policy, ensuring the council signs off on both the motion fidelity and the ledger append target before it becomes part of the SSOT.
3. **Scrollstream invariants** — The DAO export request pins the append target to `ledger/federation.jsonl`; no capsule can redirect the stream without a policy update, keeping downstream replay agents synchronized on the same ZERO_DRIFT state history.

### Proof Binding Anchor
- The canonical export payload generated by `scripts/capsules/qube_patent_pipeline.py` is hashed with SHA-256 to produce the proof binding anchor (`sha256:<digest>`). This digest appears in both the `dao.export.requested` and `capsule.sealed` ledger entries, creating a single immutable link between the export request, the ledger append target, and the ZERO_DRIFT gate results.
- The payload includes the P3L references (`DEFAULT_P3L_SOURCE` and `DEFAULT_P3L_REF`) alongside the SSOT policy (`P3L.v6`) so the anchor captures the exact semantics that produced the seal. Any change to the policy URN, attestation quorum, or motion hashes generates a new digest and immediately surfaces drift.

### Proof → Flow → Execution Mapping
- **Proof**: The council seal writes the proof binding anchor, Merkle proof, and quorum attestation into the ledger, mathematically tying the ZERO_DRIFT assertions to the export payload and SSOT policy.
- **Flow**: Avatar handoff honors the ZERO_DRIFT lock by routing through the defined append target and policy gates; operators can trace every hop back to the proof binding anchor without ambiguity.
- **Execution**: Capsules materialize assets under the enforced ZERO_DRIFT constraints, emitting frame-accurate motion ledgers, rendering the approved clips, and returning the outputs to the SSOT with the same anchor referenced in the proof step.

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

