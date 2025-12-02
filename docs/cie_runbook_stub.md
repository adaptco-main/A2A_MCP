# CIE-V1 Synthetic Perturbation Runbook (Stub)

This stub documents the operational boundary for the `content.integrity.eval.v1`
sandbox. The cell exists solely to stress-test truthful, sourced statements
with **neutral, mechanical perturbations**. No persuasion levers, adversarial
personas, or real-user data are ever permitted. All runtime behaviors must
conform to ZERO-DRIFT, DK-1.0, and MIAP controls reflected in
`manifests/content_integrity_eval.json`.

## 1. Purpose & Scope

- **Objective** – Quantify comprehension loss, citation traceability, and logical
  coherence after controlled perturbations.
- **Audience** – Research (scenario design), Platform Ops (runtime), Governance
  Council (approvals), Trust & Safety (control attestation).
- **Excluded** – Antagonist, memetic, or behavioral-influence models; any
  scenario touching personal data or unsourced claims.

## 2. Core Safeguards

1. **Synthetic Agents Only** – Parameterized templates; personalization disabled.
2. **Transparent Provenance** – Ingress artifacts require council review and
   ledger attestation before execution.
3. **Sealed I/O** – Artifact ingress only; egress limited to aggregate metrics and
   ledger updates.
4. **Neutral Perturbations** – Only the two sanctioned modules may execute under the
   `operationalDirectives.allowed_modules` list:
   - `synthetic.noise.injector.v1` (SNI) for reversible channel noise with the
     ZERO-DRIFT runtime hooks.
   - `synthetic.contradiction.synth.v1` (SCS) for structured logical probes that
     respect MIAP telemetry caps.
5. **Aggregate Observability** – Telemetry restricted to the metric set defined in
   the manifest. No per-agent state leaves the cell.

## 3. Module Summaries

| Module | Purpose | Default Controls | Output Metrics |
| ------ | ------- | ---------------- | -------------- |
| SNI (`synthetic.noise.injector.v1`) | Apply OCR blur, token drop, translation rounds, synonym swaps within neutral bounds. | ZERO-DRIFT neutrality suite; DK-1 persona isolation; runtime hooks: `pre_run_zero_drift_attestation`, `post_run_neutrality_receipt` | `semantic_similarity`, `readability_delta` |
| SCS (`synthetic.contradiction.synth.v1`) | Generate mutually exclusive counter-assertions from approved sources. | ZERO-DRIFT logical consistency; MIAP telemetry minimization; runtime hooks: `pre_run_zero_drift_attestation`, `post_run_neutrality_receipt` | `mutual_exclusivity`, `confidence_consistency`, `citation_traceability` |

### 3.1 Test Vectors and Perturbation Envelopes

- **Benign** – Single-source statements with neutral tone and default SNI knobs
  (`ocr_blur=0.10`, `token_drop=0.02`, `translation_rounds=2`, `synonym_swap=0.05`).
- **Edge** – Multi-clause statements or dense citations with elevated but bounded
  noise (`ocr_blur≤0.20`, `token_drop≤0.08`, `translation_rounds≤3`, `synonym_swap≤0.10`).
- **Adversarial** – Structured contradictions and tightly scoped source tension
  routed through SCS; expected to surface `mutual_exclusivity=true` without
  exceeding neutrality thresholds.

| Module | Perturbation Intensity | Expected Neutrality Bounds |
| ------ | ---------------------- | -------------------------- |
| SNI (`synthetic.noise.injector.v1`) | OCR blur 0.05–0.20; token drop 0.00–0.08; translation rounds 0–3; synonym swap 0.00–0.10 | `semantic_similarity ≥ 0.85`; `readability_delta ≤ 6.5`; ZERO-DRIFT variance ≤0.0002ms |
| SCS (`synthetic.contradiction.synth.v1`) | 1–5 assertions with at least 1 trusted URI; contradictory pairs seeded from approved registries | `mutual_exclusivity` flagged only on genuine conflicts; `confidence_consistency ≥ 0.90`; `citation_traceability ≥ 0.90` |

## 3.2 Neutral Perturbation Workflow

1. **SNI pass** – Execute `synthetic.noise.injector.v1` with default knobs (`ocr_blur=0.1`, `token_drop=0.02`, `translation_rounds=2`, `synonym_swap=0.05`). Capture semantic/readability deltas and attach SHA-256 receipts.
2. **SCS pass** – Feed SNI outputs plus approved source URIs into `synthetic.contradiction.synth.v1`. Validate mutual exclusivity proofs and citation coverage.
3. **Neutrality attestation** – Execute the mandated runtime hooks and store module run metadata plus DK-1.0 variance results in `ledger://cie_v1/neutrality_receipts.jsonl` before exposing aggregate metrics.
4. **Governance sign-off** – Confirm MIAP telemetry bounds, ZERO-DRIFT gates, and council quorum prior to releasing any reports.

Knob defaults follow the manifest (e.g., `ocr_blur=0.1`, `token_drop=0.02`,
`translation_rounds=2`, `synonym_swap=0.05`). Any deviation requires council
pre-approval and a refreshed neutrality scorecard.

## 4. Audit Input Package (CIE-V1)

- **Location** – `inputs/cie_v1_smoke/`
- **Format** – Line-delimited JSON payloads, each containing a Noise Injector
  request (`noise_request`) and a paired Contradiction Synthesizer request
  (`contradiction_request`).
- **Routing** – Follow the manifest’s execution order:
  1. `synthetic.noise.injector.v1` → apply neutral noise using the defaults in
     `manifests/content_integrity_eval.json#input_profile.perturbation_defaults`.
  2. `synthetic.contradiction.synth.v1` → probe logical consistency against the
     same sourced claim set.
- **Acceptance Gates** – Runs must satisfy the manifest thresholds: semantic
  similarity ≥0.85, readability delta ≤6.5, citation traceability ≥0.90, and
  confidence consistency ≥0.90.

### 4.1 Test Vectors

| ID | Description | Inputs | Expected Outcome |
| -- | ----------- | ------ | ---------------- |
| `cie_v1_smoke_benign` | Short, well-sourced procedural step. | Mild noise + two corroborating sources. | Pass: high similarity, full traceability. |
| `cie_v1_smoke_edge` | Multi-sentence claim with translation stress. | Higher blur + translation rounds, diverse sources. | Pass with minor readability delta; traceability must stay ≥0.90. |
| `cie_v1_smoke_adversarial` | Attempted contradiction on maintenance interval. | Token drop + synonym swaps; conflicting assertions guarded by approved sources. | Must flag mutual exclusivity; remain within neutrality gates. |

### 4.2 Execution (Smoke Run)

```bash
python runtime/simulation/content_integrity_eval_harness.py \
  --input-dir inputs/cie_v1_smoke \
  --manifest manifests/content_integrity_eval.json \
  --output artifacts/cie_v1_smoke.metrics.jsonl
```

- **Harness behavior** – The stub harness emits deterministic placeholder
  metrics near the manifest gates to validate routing, logging, and ledger
  paths without invoking real perturbation models.

- **Logs/Receipts** – Metrics and neutrality receipts should append to
  `artifacts/cie_v1_smoke.metrics.jsonl` and `ledger://cie_v1/neutrality_receipts.jsonl`.
- **Review** – Governance Council reviews the output against the acceptance
  gates before any publication.

## 5. Stakeholder Briefing Checklist (Summary View)

| Priority | Responsible Role | Workflow Step |
| --- | --- | --- |
| Maintain ZERO-DRIFT neutrality across perturbations | Platform Ops + Trust & Safety | Run the required hooks (`pre_run_zero_drift_attestation`, `post_run_neutrality_receipt`) and verify neutrality receipts in `ledger://cie_v1/neutrality_receipts.jsonl`. |
| Preserve MIAP-compliant telemetry and sealed ingress/egress | Platform Ops | Enforce manifest `ingressControls` (approved registries, quorum, hashing) and block any non-sanctioned modules. |
| Stress comprehension stability with reversible noise | Research + Platform Ops | Execute SNI with default envelopes from `manifests/content_integrity_eval.json#input_profile.perturbation_defaults`. |
| Probe logical consistency with sourced contradictions | Research + Governance Council | Route SCS runs using approved URIs, confirm citation coverage, and surface mutual exclusivity flags for council sign-off. |
| Publish aggregate-only results with traceability | Governance Council | Validate acceptance thresholds, attach audit receipts to `ssot://ledger/content.integrity.eval.v1/`, and approve reporting. |

## 6. Roles & Responsibilities

- **Platform Ops** – Maintain sandbox cell, enforce sealed ingress/egress,
  triage incidents.
- **Research** – Draft factual statements, configure perturbation envelopes,
  interpret aggregate metrics.
- **Governance Council** – Approve ingress artifacts, sign ledger entries,
  enforce quorum (≥4 of 6) per manifest.
- **Trust & Safety** – Verify DK-1.0 / MIAP attestations, confirm neutral module
  scorecards.

## 7. Run Lifecycle

1. **Ingress Review** – Research submits sourced statements + allowed URIs.
   Council validates provenance and records approval in the ledger.
2. **Bundle Assembly** – Ops binds synthetic agent presets with SNI/SCS default
   knobs. Capture SHA-256 hashes for artifacts per manifest logging schema.
3. **Control Verification** – Execute DK-1 persona isolation, MIAP telemetry
   minimization, and ZERO-DRIFT neutrality suites for SNI and SCS. Archive
   receipts alongside module configs.
4. **Execution** – Launch sandbox cell. Apply SNI perturbations, then SCS
   contradictions. Ensure no additional modules are scheduled.
5. **Metric Collection** – Emit aggregate time series only: comprehension loss
   (`semantic_similarity`), readability delta, traceability ratio, mutual
   exclusivity, and confidence consistency. Guard against comprehension loss
   >0.15, traceability <0.90, or coherence <0.90; flag runs breaching bounds.
6. **Ledger Finalization** – Append run metadata, approvals, metric summaries,
   and neutrality receipts to `ssot://ledger/content.integrity.eval.v1/`.

## 8. Outstanding Tasks

- Automate ZERO-DRIFT neutrality scorecards for SNI and SCS, persisting outputs to `governance/scorecards/cie_v1_neutrality.md`.
- Publish simulation harness (`runtime/simulation/content_integrity_eval_harness.py`)
  with governance replay hooks.
- Author failure playbooks and escalation contacts.
- Add automated threshold enforcement prior to council sign-off.

> **Status** – Stub. Update as the automation artifacts and harness mature.
