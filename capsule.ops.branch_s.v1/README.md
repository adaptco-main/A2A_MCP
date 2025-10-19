# Capsule Ops Toolkit — Branch-S (Sentinel Epoch)

## Overview
This toolkit orchestrates the full lifecycle of the Sentinel branch operations
within the QLOCK Sovereign System:

1. **Apply & Seal** — Creates and seals a new Sentinel-anchored trust path.
2. **Revoke** — Issues a controlled rollback and lineage-preserving revocation.
3. **Reissue** — Initiates a new trust epoch under Sentinel authority.
4. **Federate** — Propagates the new epoch across DAO federation endpoints.

## Commands
```bash
make branch-s apply
make branch-s revoke
make branch-s reissue
make branch-s federate
```

## Ledger Outputs

All ledger entries are appended to `ledger.branch_s.jsonl`.

Each run emits:

* `manifest.json`
* `gate_report.json`
* `capsule.federation.receipt.v1.json` or `capsule.reissue.receipt.v1.json`
* Hash archive (`checksums.sha256`, `revoke.sha256`, `reissue.sha256`)

## Federation Integration

Federation relay uses `BEARER_TOKEN` from the environment:

```bash
export BEARER_TOKEN=<token>
make branch-s federate
```

---

### 🪶 Optional Hardening (if you want full CI/CD integration)

- Add a `.github/workflows/branch_s.yml` for automated Sentinel trust reissue.  
- Wire the `make branch-s federate` target to your orchestrator’s CI secret token.  
- Add checksum verification (`sha256sum -c`) at workflow exit to guarantee immutability.

---

Would you like me to generate the **GitHub Actions workflow YAML** next — so that the Sentinel apply/revoke/reissue cycle runs automatically on merge to `main` or manual trigger via `workflow_dispatch`?
