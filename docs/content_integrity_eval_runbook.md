# content.integrity.eval.v1 Sandbox Runbook (Stub)

This document tracks the initial operational framing for the
`content.integrity.eval.v1` sandbox cell. The sandbox exists purely to
measure how well truthful information survives bounded distortion when only
synthetic, parameterized agents are present. No real users or external data
sources ever interact with this environment.

## 1. Purpose and Scope

- **Objective**: Evaluate robustness of truthful statements when exposed to
  configurable channel noise inside a sealed orchestration cell.
- **Audience**: Research (experiment design), Trust & Safety (controls),
  Governance Council (oversight), and Platform Ops (runtime maintenance).
- **Out of Scope**: Any experimentation that touches real-person identifiers
  or personalized prompts.

## 2. Core Safeguards

1. **Synthetic Agents Only** — Personas are generated from templated parameter
   sets and may not ingest scraped profiles.
2. **Transparent Provenance** — Every stimulus bundle carries council review
   attestations and immutable ledger receipts.
3. **Sealed I/O** — Ingress is artifact-only; egress is limited to aggregate
   robustness metrics and append-only ledger updates.
4. **Noise as Measurement Tool** — Channel noise is applied strictly as a
   robustness probe. Persuasive levers are disallowed.

## 3. Roles & Responsibilities

- **Platform Ops**: Maintain the sandbox cell, enforce sealed ingress/egress,
  and respond to incidents.
- **Research**: Define synthetic agent parameters, configure channel noise, and
  interpret aggregate metrics.
- **Governance Council**: Approve scenario bundles, review ledger outputs, and
  gate releases.
- **Trust & Safety**: Monitor DK-1.0 and MIAP attestations, ensure telemetry
  minimization.

## 4. Run Lifecycle (Draft)

1. **Bundle Preparation** — Research assembles synthetic agent presets, noise
   envelopes, and truth probes. Council pre-approves artifacts.
2. **Control Verification** — DK-1.0 persona isolation and MIAP telemetry
   minimization checks must pass (scripts forthcoming).
3. **Execution** — Orchestrator binding launches the sandbox cell using the
   approved bundle identifier.
4. **Observation** — Metrics collector streams aggregate robustness metrics to
   governance dashboards. No per-agent traces leave the cell.
5. **Ledger Finalization** — Append run metadata, approvals, and aggregate
   outputs to the immutable ledger store.

## 5. Observability & Reporting

- **Metrics Collector**: Emits only aggregate series prefixed with
  `aggregate.truth_survival.*`.
- **Ledger**: Append-only JSONL file capturing council approvals, control
  attestations, run metadata, and aggregate metric digests.
- **Dashboards**: Governance-only dashboards consume aggregate metrics for
  compliance reviews.

## 6. Outstanding Work

- Deliver automation scripts for DK-1.0 and MIAP control verification.
- Publish simulation harness (`runtime/simulation/content_integrity_eval_harness.py`)
  with council/audit replay hooks.
- Document failure playbooks and escalation contacts.
- Define regression scenarios for future epochs once approved.

> **Status**: Stub. Update alongside manifest changes and automation
> deliverables.
