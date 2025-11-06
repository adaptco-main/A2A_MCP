# CIE-V1 Operational Runbook

## Overview
The Content Integrity Evaluation service (CIE-V1) validates narrative payloads using **neutral perturbation** techniques that preserve the ZERO-DRIFT mandate. The stack now runs exclusively on two synthetic modules:

1. `synthetic.noise.injector.v1` — generates distribution-preserving neutral noise samples.
2. `synthetic.contradiction.synth.v1` — builds minimally divergent contradiction narratives for resilience checks.

Both modules emit deterministic hashes into the ledger anchor declared in `manifests/services/content_integrity_eval.json` to keep audits replayable.

## Pre-flight Checklist
- Confirm the anchor ledger `ledger/content_integrity_eval` is writable and hash-chain verified.
- Load the council-approved neutral perturbation presets (`clamp_sigma`, `neutrality_score_threshold`, `neutrality_floor`).
- Validate the operator keypair for attestation signing (`ecdsa-secp256k1`).
- Ensure ZERO-DRIFT monitors are green in the cockpit dashboard.

## Execution Flow
1. **Ingest** the narrative payload and bind a `noise_seed` plus `nonce`.
2. **Noise Injection**
   - Dispatch to `synthetic.noise.injector.v1` with configured perturbation budget.
   - Collect `samples` (JSONL) and the `variance_report` summary.
   - Verify the canonical hash matches ledger expectations before proceeding.
3. **Contradiction Synthesis**
   - Feed the baseline payload plus curated `knowledge_refs` into `synthetic.contradiction.synth.v1`.
   - Capture the `contradiction_set` and `consistency_metrics`.
   - Confirm neutrality floor and drift monitor readings stay within policy bounds.
4. **Aggregate Metrics**
   - Compute `entropy_ldi`, `coherence_chrono_mi`, and `yield_kl_gain` for reporting.
   - Write the attested result bundle with the module output hashes.

## Post-run Attestation
- Append the run metadata to the ledger with `prev_hash` linkage.
- Sign the `.anchor.json` entry using the service ECDSA key.
- Store both module output manifests alongside the run record for replay.

## Incident Response
- **Neutrality breach detected:** Pause both modules, reset seeds, notify Ethics Desk, and rerun the latest batch after calibration.
- **Ledger mismatch:** Trigger a replay job; if divergence persists, invalidate the run and restore from the last trusted anchor.
- **Module failure:** Fail closed, redeploy the affected module from the sealed artifact store, and re-verify hashes before resuming operations.

Maintain this runbook within the SSOT pipeline; any edits require Ethics Desk sign-off before deployment.
