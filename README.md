# Core Orchestrator Governance Pilot

> **Developer note.**
> * Signing is performed with [`cosign sign-blob`](https://github.com/sigstore/cosign). For development you can supply `SIGNER=/path/to/mock_cosign` when running the freeze or pilot scripts.
> * Ledger interactions default to `http://localhost:3000`. Export `LEDGER_BASE_URL` to point at a real registry when wiring into production infrastructure.
> * Hardware-backed signing and long-term ledger persistence are not implemented. The in-memory ledger client in `server/index.js` is a drop-in seam for real HSM and registry integrations.

## Repository layout

| Path | Purpose |
| --- | --- |
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
