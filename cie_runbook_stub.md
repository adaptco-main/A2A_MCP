# CIE-V1 Neutral Perturbation Runbook Stub

This stub documents the operational posture for the `content.integrity.eval.v1` stack after migrating to neutral perturbation models.

## Service Overview
- **Scope:** Validate narrative assets against ZERO-DRIFT policy using synthetic perturbations.
- **Primary Modules:**
  - `synthetic.noise.injector.v1`
  - `synthetic.contradiction.synth.v1`
- **Control Plane:** World OS Content Integrity Evaluation Service (CIE-V1).

## Module Responsibilities
### synthetic.noise.injector.v1
- Injects calibrated, policy-safe neutral noise onto candidate payload windows.
- Enforces amplitude bounds of ±0.03 with a flat spectral distribution.
- Rejects profiles that introduce adversarial bias or semantic drift.

### synthetic.contradiction.synth.v1
- Derives contradiction prompts from the perturbed payload stream and fact index.
- Limits output to five contradiction probes per window.
- Records each probe in `contradiction.audit.log` for downstream compliance review.

## Operational Procedure
1. **Ingest Payload**
   - Load the sample window into the evaluation buffer.
   - Verify metadata checksum and provenance tokens.
2. **Apply Neutral Noise**
   - Select the matching entry from `noise.profile.catalog`.
   - Execute `synthetic.noise.injector.v1` and archive the resulting `payload.sample.window.perturbed` artifact.
3. **Synthesize Contradictions**
   - Feed the perturbed window and `semantic.fact.index` into `synthetic.contradiction.synth.v1`.
   - Persist generated probes and the audit log payload.
4. **Score ZERO-DRIFT**
   - Compute drift variance and contradiction density across the probe set.
   - Emit telemetry to `cie.v1.anchor.zero_drift`.
5. **Review Alerts**
   - Trigger corrective playbooks if zero-drift exceeds 0.05 or contradiction density exceeds 0.35.

## Compliance Notes
- All perturbations must remain reversible; do not write back to primary content stores.
- Personal data injection and policy override attempts constitute critical failures.
- Seal attestation logs with the updated `INTUNE.Zero_Drift_V1` reference.

## Telemetry & Reporting
- Dashboards: `dashboard.cie.zero_drift_overview`, `dashboard.cie.synthetic_probe_depth`.
- Weekly export audit: include noise profiles applied, contradiction counts, and remediation tickets.
- File vulnerability reports referencing ZERO-DRIFT monitor checkpoints when thresholds are breached.
