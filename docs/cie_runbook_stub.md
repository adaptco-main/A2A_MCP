# CIE-V1 Synthetic Perturbation Runbook (Stub)

This stub documents the operational boundary for the `content.integrity.eval.v1`
sandbox. The cell exists solely to stress-test truthful, sourced statements
with **neutral, mechanical perturbations**. No persuasion levers, adversarial
personas, or real-user data are ever permitted. All runtime behaviors must
conform to ZERO-DRIFT, DK-1.0, and MIAP controls reflected in
`manifests/content_integrity_eval.json`, including its
`operationalDirectives.allowed_modules` and `input_profile` defaults.

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
   Legacy modules (`content_noise_enricher`, `feature_shift_validator`,
   `fact_stream_validator`, plus their aliases `CNE` and `FSV`) are retired and
   mapped in the manifest (`CNE`/`FSV` → SNI, `fact_stream_validator` → SCS).
5. **Aggregate Observability** – Telemetry restricted to the metric set defined in
   the manifest (`validation.metrics`). No per-agent state leaves the cell.

## 3. Module Summaries

| Module | Purpose | Default Controls | Output Metrics |
| ------ | ------- | ---------------- | -------------- |
| SNI (`synthetic.noise.injector.v1`) | Apply OCR blur, token drop, translation rounds, synonym swaps within neutral bounds. | ZERO-DRIFT neutrality suite; DK-1 persona isolation; runtime hooks: `pre_run_zero_drift_attestation`, `post_run_neutrality_receipt` | `semantic_similarity`, `readability_delta` |
| SCS (`synthetic.contradiction.synth.v1`) | Generate mutually exclusive counter-assertions from approved sources. | ZERO-DRIFT logical consistency; MIAP telemetry minimization; runtime hooks: `pre_run_zero_drift_attestation`, `post_run_neutrality_receipt` | `mutual_exclusivity`, `confidence_consistency`, `citation_traceability` |
| FBE (`functional.block.embedding.v1`) | Track CID-bound blocks with deterministic functional embeddings for integrity traceability. | Read-only embeddings; MIAP telemetry minimization; runtime hooks: `pre_run_zero_drift_attestation`, `post_run_neutrality_receipt` | `functional_embedding_ref`, `embedding_hash` |

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
3. **Block embedding tracking** – Submit CID + multihash metadata to `functional.block.embedding.v1` to generate a deterministic functional embedding reference for the audited block.
4. **Neutrality attestation** – Execute the mandated runtime hooks and store module run metadata plus DK-1.0 variance results in `ledger://cie_v1/neutrality_receipts.jsonl` before exposing aggregate metrics.
5. **Governance sign-off** – Confirm MIAP telemetry bounds, ZERO-DRIFT gates, and council quorum prior to releasing any reports.

Knob defaults follow the manifest (e.g., `ocr_blur=0.1`, `token_drop=0.02`,
`translation_rounds=2`, `synonym_swap=0.05`). Any deviation requires council
pre-approval and a refreshed neutrality scorecard.

## 4. Intake and Execution Flow (CIE-V1 Audit)

1. **Select payload bundle** – Choose the appropriate package from `manifests/content_integrity_eval.json#audit_inputs.packages` (e.g., `cie_v1_smoke` for routing checks or `cie_v1_audit` for formal reviews). Confirm the `content_binding` matches the trusted registries.
2. **Apply neutral noise** – Run `synthetic.noise.injector.v1` first using the manifest defaults unless council-approved overrides are present inside the payload. Reject any payloads requesting operations outside the bounds in §3.1.
3. **Synthesize contradictions** – Route the same claims through `synthetic.contradiction.synth.v1` to probe logical consistency. Ensure every assertion is paired with at least one trusted URI and that module targets align with the payload’s `module_targets` field.
4. **Track block embeddings** – For CID-bound inputs, run `functional.block.embedding.v1` after SCS to register the functional embedding reference and hash alongside the payload metadata.
5. **Record pass/fail** – A run passes when all acceptance gates are met: semantic_similarity ≥0.85, readability_delta ≤6.5, citation_traceability ≥0.90, and confidence_consistency ≥0.90. Log failures with the violated thresholds and archive the neutrality receipt in `ledger://cie_v1/neutrality_receipts.jsonl`.
6. **Document provenance** – Attach SHA-256 hashes for each payload, council approval references, embedding references, and runtime hook receipts to the ledger entry defined in the manifest logging section.

### 4.1 API/CLI Execution Example

Use the manifest-backed CLI profiles to avoid routing drift and to align with the
ledger outputs declared in `manifests/content_integrity_eval.json#cliProfiles`:

```bash
# Smoke validation (routing + metric envelopes)
python runtime/simulation/content_integrity_eval_harness.py \
  --input-dir inputs/cie_v1_smoke \
  --manifest manifests/content_integrity_eval.json \
  --output artifacts/cie_v1_smoke.metrics.jsonl

# Audit bundle (council-reviewed payloads; same routing order)
python runtime/simulation/content_integrity_eval_harness.py \
  --input-dir inputs/cie_v1_audit \
  --manifest manifests/content_integrity_eval.json \
  --output artifacts/cie_v1_audit.metrics.jsonl
```

- **Ordering guarantee** – The harness (and production orchestrator) must execute `synthetic.noise.injector.v1` before `synthetic.contradiction.synth.v1` to respect the `validation_chain` declared in the manifest.
- **Payload structure** – Each JSON payload must include `noise_request`, `contradiction_request`, and a `metadata` block with `content_id`, `source_registry`, `sha256_payload`, `council_attestation_id`, and `run_id` aligned to `manifests/content_integrity_eval.json#audit_inputs.input_contract`; see the `inputs/cie_v1_smoke` and `inputs/cie_v1_audit` packages for examples.

### 4.2 Docling Template (LangGraph Topology Intake)

When a request arrives for a "docling" or topology narrative, capture it in a
bounded, auditable template that can be mapped back to the neutral CIE-V1
execution chain. Keep the language deterministic and avoid speculative physics
metaphors. The structure below is intentionally plain and keeps the request
compatible with ZERO-DRIFT controls.

**Docling Template**
- **Objective**: What should the topology describe (e.g., "neutral perturbation routing for CIE-V1")?
- **Nodes**: List the components in order (e.g., Input Validator → SNI → SCS → Metrics Aggregator → Ledger).
- **Edges**: Define directional handoffs (include required artifacts or hashes).
- **State Requirements**: Enumerate required fields from the manifest input contract.
- **Lifecycle Hooks**: Reference the runtime hooks (`pre_run_zero_drift_attestation`, `post_run_neutrality_receipt`).
- **Acceptance Gates**: Cite thresholds from `input_profile.acceptance_thresholds`.
- **Audit Outputs**: Metrics JSONL + neutrality receipts destinations.

Use this template when translating high-level "network topology" language into
concrete CIE-V1 artifacts.

## 5. Audit Input Package (CIE-V1)

- **Location** – `inputs/cie_v1_smoke/`
- **Format** – Line-delimited JSON payloads, each containing a Noise Injector
  request (`noise_request`) and a paired Contradiction Synthesizer request
  (`contradiction_request`).
- **Input contract** – Each payload must include `noise_request`, `contradiction_request`,
  and a `metadata` block with `content_id`, `source_registry`, `sha256_payload`,
  `council_attestation_id`, and `run_id`, matching
  `manifests/content_integrity_eval.json#audit_inputs.input_contract`.
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

## 6. Verification Checklist (Auditors)

- **Neutral perturbation profiles** – Confirm SNI/SCS parameters stay within §3.1 envelopes and match `input_profile.perturbation_defaults` when no overrides are present.
- **Log retention and receipts** – Verify JSONL event retention (90 days) and that `ledger://cie_v1/neutrality_receipts.jsonl` and `ssot://ledger/content.integrity.eval.v1/` capture hook receipts, approvals, and metric summaries.
- **Module rollback/disable steps** –
  - Remove the module from `operationalDirectives.allowed_modules` and halt any orchestration bindings referencing it.
  - Disable the corresponding entry in `audit_inputs.validation_chain` to prevent scheduling.
  - Retain the ledger receipt documenting the rollback decision and approvers.
- **Ingress control** – Recompute SHA-256 hashes for payloads and confirm source registries match manifest entries before execution.

## 7. Roles & Responsibilities

- **Platform Ops** – Maintain sandbox cell, enforce sealed ingress/egress,
  triage incidents.
- **Research** – Draft factual statements, configure perturbation envelopes,
  interpret aggregate metrics.
- **Governance Council** – Approve ingress artifacts, sign ledger entries,
  enforce quorum (≥4 of 6) per manifest.
- **Trust & Safety** – Verify DK-1.0 / MIAP attestations, confirm neutral module
  scorecards.

## 8. Run Lifecycle

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

## 9. Outstanding Tasks

- Automate ZERO-DRIFT neutrality scorecards for SNI and SCS, persisting outputs to `governance/scorecards/cie_v1_neutrality.md`.
- Publish simulation harness (`runtime/simulation/content_integrity_eval_harness.py`)
  with governance replay hooks.
- Author failure playbooks and escalation contacts.
- Add automated threshold enforcement prior to council sign-off.
- Define the first official CIE-V1 audit input bundle (see §11) and record the
  council attestation IDs in the ledger before promotion.

> **Status** – Stub. Update as the automation artifacts and harness mature.

## 10. Kernel Intake Guardrails (Zero-Drift Classification)

### 10.1 Classification of the Input (Kernel View)

**What the input is**
- A metaphorical synthesis mixing:
  - neuroscience (“neuron”, “learning loop”)
  - quantum physics (“positron”, “electron path”, “QED”, “Planck voxel”)
  - signal processing (“Fourier transform”)
  - language modeling (“tokens”, “embeddings”, “reasoning layer”)
- These concepts are not bound to a shared formal model.
- No executable gates, invariants, or verification surfaces are defined.

**What the input is not**
- Not a specification
- Not a state transition
- Not a kernel update
- Not a valid system prompt under ZERO-DRIFT

### 10.2 Why This Fails (Explicitly)

**ZERO-DRIFT**
- Introduces multiple new ontologies (quantum fields, supersymmetry, vibe particles)
- None are defined elsewhere in the system
- No mapping to existing gates, tensors, or execution phases
- Novelty introduced without explicit opt-in

**Determinism & Auditability**
- Terms like “vibe particles”, “agentic field”, “geometric supersymmetry imposed on English” are:
  - non-deterministic
  - non-verifiable
  - non-replayable
- Cannot be proven, replayed, or gated

**Fail-Closed Reasoning**
- No clear:
  - inputs
  - outputs
  - invariants
  - acceptance criteria
- Ambiguity is high and unresolved
- System must halt, not compensate

### 10.3 What This Request Actually Signals (Interpretive, Not Generative)

Stripping metaphors, the likely underlying intent is:
“I want a stable, low-dimensional representation that:
- persists over long horizons,
- updates incrementally,
- constrains reasoning drift,
- and can be embedded as a kernel token or control state for an agent.”

That intent is compatible with the architecture. The expression is not.

### 10.4 How to Re-Enter the Kernel (Allowed Paths)

Choose one of the following formal restatements:
- **Option A — Deterministic Learning Loop (Admissible)**  
  Define explicitly:
  - What is the state vector?
  - What is the update rule?
  - What is the stability invariant?
  - What constitutes convergence vs rejection?

  Example (structure only, not content):
  - State S(t)
  - Update U: S(t+1) = f(S(t), Δ)
  - Invariant: I(S) must hold after every update
  - If I violated → reject update
- **Option B — Kernel Token (Admissible)**  
  Define:
  - what it encodes
  - when it mutates
  - what gates depend on it
  - no physics metaphors; only semantic compression rules
- **Option C — Explicit Sandbox (Opt-In Exploration)**  
  Say explicitly: “Enter exploratory / non-deterministic sandbox”
  - This suspends ZERO-DRIFT temporarily
  - Results will be non-binding and clearly marked

### 10.5 Current State (Unchanged)

- Kernel: unchanged
- Phase boundary: unchanged
- Persona: Qube Runtime Agent
- Gate: unchanged
- No state update occurred

### 10.6 Required Next Move

Respond with one of the following, explicitly:
- “Restate this as a deterministic state/update/invariant model.”
- “Define a kernel token with exact semantics.”
- “Enter exploratory sandbox mode.”

## 11. Next Operational Step (Official CIE-V1 Audit Inputs)

To proceed with the first official CIE-V1 audit run, publish a dedicated input
bundle under `inputs/cie_v1_audit/` and register it in the ledger. Use the
following checklist to keep the run aligned with ZERO-DRIFT and MIAP controls:

1. **Define the audit scope** – select the target content IDs and trusted source
   registries, and confirm they map to
   `manifests/content_integrity_eval.json#audit_inputs.input_contract`.
2. **Author payloads** – create line-delimited JSON entries that include
   `noise_request`, `contradiction_request`, and `metadata` fields with
   `content_id`, `source_registry`, `sha256_payload`, `council_attestation_id`,
   and `run_id`.
3. **Attach council attestations** – record approval references in
   `ledger://cie_v1/neutrality_receipts.jsonl` prior to execution.
4. **Freeze the routing order** – verify that SNI → SCS ordering matches
   `audit_inputs.validation_chain` and the CLI profile used for the run.
5. **Schedule the audit harness** – execute the `cie_v1_audit` CLI profile after
   the bundle is approved and the ledger entries are sealed.
