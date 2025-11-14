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
4. **Neutral Perturbations** – Only the two sanctioned modules may execute:
   - `synthetic.noise.injector.v1` (SNI) for reversible channel noise.
   - `synthetic.contradiction.synth.v1` (SCS) for structured logical probes.
5. **Aggregate Observability** – Telemetry restricted to the metric set defined in
   the manifest. No per-agent state leaves the cell.

## 3. Module Summaries

| Module | Purpose | Default Controls | Output Metrics |
| ------ | ------- | ---------------- | -------------- |
| SNI (`synthetic.noise.injector.v1`) | Apply OCR blur, token drop, translation rounds, synonym swaps within neutral bounds. | ZERO-DRIFT neutrality suite; DK-1 persona isolation | `semantic_similarity`, `readability_delta` |
| SCS (`synthetic.contradiction.synth.v1`) | Generate mutually exclusive counter-assertions from approved sources. | ZERO-DRIFT logical consistency; MIAP telemetry minimization | `mutual_exclusivity`, `confidence_consistency`, `citation_traceability` |

## 3.1 Neutral Perturbation Workflow

1. **SNI pass** – Execute `synthetic.noise.injector.v1` with default knobs (`ocr_blur=0.1`, `token_drop=0.02`, `translation_rounds=2`, `synonym_swap=0.05`). Capture semantic/readability deltas and attach SHA-256 receipts.
2. **SCS pass** – Feed SNI outputs plus approved source URIs into `synthetic.contradiction.synth.v1`. Validate mutual exclusivity proofs and citation coverage.
3. **Neutrality attestation** – Store module run metadata and DK-1.0 variance results in `ledger://cie_v1/neutrality_receipts.jsonl` before exposing aggregate metrics.
4. **Governance sign-off** – Confirm MIAP telemetry bounds, ZERO-DRIFT gates, and council quorum prior to releasing any reports.

Knob defaults follow the manifest (e.g., `ocr_blur=0.1`, `token_drop=0.02`,
`translation_rounds=2`, `synonym_swap=0.05`). Any deviation requires council
pre-approval and a refreshed neutrality scorecard.

## 4. Roles & Responsibilities

- **Platform Ops** – Maintain sandbox cell, enforce sealed ingress/egress,
  triage incidents.
- **Research** – Draft factual statements, configure perturbation envelopes,
  interpret aggregate metrics.
- **Governance Council** – Approve ingress artifacts, sign ledger entries,
  enforce quorum (≥4 of 6) per manifest.
- **Trust & Safety** – Verify DK-1.0 / MIAP attestations, confirm neutral module
  scorecards.

## 5. Run Lifecycle

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

## 6. Outstanding Tasks

- Automate ZERO-DRIFT neutrality scorecards for SNI and SCS, persisting outputs to `governance/scorecards/cie_v1_neutrality.md`.
- Publish simulation harness (`runtime/simulation/content_integrity_eval_harness.py`)
  with governance replay hooks.
- Author failure playbooks and escalation contacts.
- Add automated threshold enforcement prior to council sign-off.

> **Status** – Stub. Update as the automation artifacts and harness mature.
