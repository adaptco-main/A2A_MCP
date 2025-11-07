# CIE-V1 Synthetic Perturbation Runbook (Stub)

This stub documents the operational boundary for the `content.integrity.eval.v1`
sandbox. The cell exists solely to stress-test truthful, sourced statements
with **neutral, mechanical perturbations**. No persuasion levers, adversarial
personas, or real-user data are ever permitted. All runtime behaviors must
conform to ZERO-DRIFT, DK-1.0, and MIAP controls reflected in
`manifests/content_integrity_eval.json`. The runbook now binds directly to the
ingress controls and validation envelopes codified in the manifest.

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
   ledger attestation before execution. Hash submissions with SHA-256 to match
   `ingressControls.artifact_hashing`.
3. **Sealed I/O** – Artifact ingress only; egress limited to aggregate metrics and
   ledger updates. Neutrality receipts must post to
   `ledger://cie_v1/neutrality_receipts.jsonl`.
4. **Neutral Perturbations** – Only the two sanctioned modules may execute:
   - `synthetic.noise.injector.v1` (SNI) for reversible channel noise.
   - `synthetic.contradiction.synth.v1` (SCS) for structured logical probes.
   Execute the ZERO-DRIFT neutrality suite before each run and attach the
   scorecard cited in the manifest.
5. **Aggregate Observability** – Telemetry restricted to the metric set defined in
   the manifest. No per-agent state leaves the cell. Track only
   `semantic_similarity`, `readability_delta`, `citation_traceability`,
   `confidence_consistency`, and `mutual_exclusivity`.

## 3. Module Summaries

| Module | Purpose | Default Controls | Output Metrics |
| ------ | ------- | ---------------- | -------------- |
| SNI (`synthetic.noise.injector.v1`) | Apply OCR blur, token drop, translation rounds, synonym swaps within neutral bounds. | ZERO-DRIFT neutrality suite; DK-1 persona isolation (defaults: `ocr_blur=0.1`, `token_drop=0.02`, `translation_rounds=2`, `synonym_swap=0.05`) | `semantic_similarity`, `readability_delta` |
| SCS (`synthetic.contradiction.synth.v1`) | Generate mutually exclusive counter-assertions from approved sources. | ZERO-DRIFT logical consistency; MIAP telemetry minimization (≥1 assertion & URI; unique source list enforced) | `mutual_exclusivity`, `confidence_consistency`, `citation_traceability` |

Knob defaults follow the manifest (e.g., `ocr_blur=0.1`, `token_drop=0.02`,
`translation_rounds=2`, `synonym_swap=0.05`). Any deviation requires council
pre-approval and a refreshed neutrality scorecard. Stay within the documented
minimum/maximum envelopes: noise probabilities ≤0.25, translation rounds ≤4.

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
   Council validates provenance, checks sources against the approved registry,
   and records approval in the ledger. Use the manifest's
   `ingressTemplates.first_audit_batch` format for the initial campaign and
   attach template hashes to the ledger record.
2. **Bundle Assembly** – Ops binds synthetic agent presets with SNI/SCS default
   knobs. Capture SHA-256 hashes for artifacts per manifest logging schema.
3. **Control Verification** – Execute DK-1 persona isolation, MIAP telemetry
   minimization, and ZERO-DRIFT neutrality suites for SNI and SCS. Archive
   receipts alongside module configs and upload neutrality scorecards.
4. **Execution** – Launch sandbox cell. Apply SNI perturbations, then SCS
   contradictions. Ensure no additional modules are scheduled.
5. **Metric Collection** – Emit aggregate time series only: comprehension loss
   (`semantic_similarity`), readability delta, traceability ratio, mutual
   exclusivity, and confidence consistency. Guard against comprehension loss
   >0.15, readability delta >6.5, traceability <0.90, or coherence <0.90; flag
   runs breaching bounds and initiate remediation playbooks.
6. **Ledger Finalization** – Append run metadata, approvals, metric summaries,
   neutrality receipts, and validation envelopes to
   `ssot://ledger/content.integrity.eval.v1/`.

## 6. Outstanding Tasks

- Automate ZERO-DRIFT neutrality scorecards for SNI and SCS.
- Publish simulation harness (`runtime/simulation/content_integrity_eval_harness.py`)
  with governance replay hooks.
- Populate the first-audit template with ≥3 sourced statements and council
  approvals for pilot verification.
- Author failure playbooks and escalation contacts.
- Add automated threshold enforcement prior to council sign-off.
- Define council workflow for first full audit batch (ingress templates + run inputs).

> **Status** – Stub. Update as the automation artifacts and harness mature.

## Appendix A – First Audit Batch Template (Excerpt)

Populate the template below for the inaugural run. Each record must hash to the
ledger entry referenced in `statement_id` and use sources from the approved
registry.

```json
[
  {
    "statement_id": "cie-audit-0001",
    "source_claim": "The Voyager 1 probe crossed the heliopause in 2012.",
    "source_uri": "https://www.nasa.gov/mission_pages/voyager/voyager20130815.html",
    "confidence": 0.98,
    "justification": "NASA press release confirming heliopause crossing in Aug 2012."
  },
  {
    "statement_id": "cie-audit-0002",
    "source_claim": "Basalt is the most common rock type on Earth's oceanic crust.",
    "source_uri": "https://www.usgs.gov/programs/VHP/basalt",
    "confidence": 0.94,
    "justification": "USGS overview on volcanic rock distribution."
  }
]
```

> Add at least one additional record before execution; council quorum must
> sign the completed list.
