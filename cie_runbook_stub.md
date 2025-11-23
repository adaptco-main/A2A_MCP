# Content Integrity Evaluation (CIE-V1) Runbook

## Overview
CIE-V1 validates content robustness while honoring the ZERO-DRIFT mandate. The stack now runs on **neutral perturbation models** only:
- **synthetic.noise.injector.v1** adds bounded, neutral perturbations to gauge drift sensitivity.
- **synthetic.contradiction.synth.v1** generates labeled contradictions to pressure-test claims without introducing unlabeled misinformation.

## Operating modes
- **Evaluate**: Ingest source content, apply neutral noise, measure drift, and synthesize contradictions for robustness scoring.
- **Export**: Emit capsule events and robustness metrics to downstream audit ledgers.

## Inputs
- `source_content`: canonical text or structured payload under evaluation.
- `perturbation_profile`: constraints for noise injection (entropy budget, allowed token scopes).
- `claim_graph`: optional structured claims for contradiction synthesis.
- `contradiction_policy`: labeling and guardrails for synthetic contradictions.

## Outputs
- `content_with_neutral_noise`: perturbed but semantically aligned payload.
- `synthetic_contradictions`: labeled contradiction set with linkage to original claims.
- `robustness_score`: roll-up metric derived from drift sensitivity and contradiction coverage.
- Capsule events with lineage (`capsule_id`, `capsule_ref`) for audit.

## Preconditions
- Service manifest `content_integrity_eval.json` deployed with both modules enabled.
- Telemetry sink reachable for ledger emission.
- Sandbox workers provisioned with least-privilege credentials.

## First CIE-V1 audit run
1. Validate manifest deployment: confirm `synthetic.noise.injector.v1` and `synthetic.contradiction.synth.v1` are active and `replaces` legacy CNE/FSV paths.
2. Prepare inputs: supply `source_content`, tuned `perturbation_profile`, and optional `claim_graph` plus `contradiction_policy`.
3. Execute evaluate flow via `capsules/content-integrity/eval.v1` interface.
4. Confirm outputs: review `robustness_score` and ensure contradictions are tagged as synthetic.
5. Verify audit artifacts: ledger emits capsule events with lineage and ZERO-DRIFT compliance notes.

## Observability
- Metrics: `drift_score`, `neutral_noise_rate`, `contradiction_coverage`, `audit_pass_rate`.
- Logging: Module invocations must include module id, input capsule references, and guardrail outcomes.
- Alerts: trigger on drift_score > threshold-neutral or missing neutrality tags on contradictions.

## Safety and rollback
- If neutrality violations occur, disable the offending module and revert to baseline evaluate path.
- Record rollback events in the ledger for traceability.
- Re-run audit after remediation to confirm ZERO-DRIFT compliance.

## Change management
- Any model updates must retain neutral perturbation guarantees and pass contradiction labeling checks.
- Update the manifest and rerun the first-audit procedure for every model promotion.
