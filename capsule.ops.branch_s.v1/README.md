# Capsule Ops Toolkit — Branch-S (Sentinel Epoch)

## Overview
The Branch-S toolkit promotes the Sol.F1 dual prompt bundle into a sovereign, auditable capsule lifecycle. Each invocation emits canonical manifests, receipts, and hashes that can be sealed, revoked, reissued, and federated under council discipline.

Core phases:

1. **Apply & Seal** – Build a fresh Scrollstream Capsule B artifact and register the Sentinel-100 epoch seal.
2. **Revoke** – Publish a lineage-preserving rollback notice with hashes of the most recent capsule digest.
3. **Reissue** – Regenerate the Scrollstream capsule and update receipts; optionally federate to external ledgers.
4. **Federate** – Invoke `reissue` with federation payload emission and bearer token hashing.

All scripts share `lib/branch_s_common.sh`, which centralizes attachment bindings, hashing utilities, and ledger emission so every phase writes to the same schema.

## Commands
```bash
make branch-s apply
make branch-s revoke
make branch-s reissue
make branch-s federate   # requires BEARER_TOKEN
make branch-s verify     # validate most recent run
make branch-s clean      # remove generated artifacts
```

## Runtime Layout
Each action produces a time-stamped run directory inside `.out/`:

```
.out/
  └── 20241007T024446Z_apply/
        manifest.json
        gate_report.json
        capsule.seal.receipt.v1.json
        capsule.prompt.designStudio.dual.v1.qcap
        checksums.sha256
        apply.sha256
```

Reissue and federation runs include additional receipts, relay payloads, and checksum mirrors. The ledger `ledger.branch_s.jsonl` records a JSON object per run with references to the run directory, artifact hashes, and federation metadata when present.

## Ledger & Receipts
* `ledger.branch_s.jsonl` – append-only JSON lines describing each action, including capsule digest and checksum hashes.
* `checksums.sha256` – generated inside each run directory and used by `make branch-s verify`.
* `*.sha256` – single-artifact digests for rapid attestations.

## Federation Integration
Federation relay uses the environment variable `BEARER_TOKEN`, hashed before it is recorded:

```bash
export BEARER_TOKEN=<token>
make branch-s federate
```

Federated runs emit `capsule.federation.receipt.v1.json`, `dao.federation.relay.json`, and `federation.response.json` alongside the capsule artifact.

## Verification & Cleanup
* `make branch-s verify` – Locates the newest run directory and replays its `checksums.sha256` file.
* `make branch-s clean` – Deletes the `.out/` tree while preserving the governance ledger.

Augment with CI (e.g., `.github/workflows/branch_s.yml`) to automate reissue + federation and assert checksum validation at workflow exit.
