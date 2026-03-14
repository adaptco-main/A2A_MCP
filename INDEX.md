# Agentic Factory System Index

This index is the root entrypoint for the Agentic Factory System release-control surfaces.

## Core Python Surfaces
- `orchestrator/release_orchestrator.py`: phase resolver and release gating signals.
- `orchestrator/runtime_bridge.py`: handshake bundle builder and runtime assignment writer.
- `orchestrator/qube_kernel_bridge.py`: signed chaos/test receipt exporter for a future `qube-kernel` consumer.
- `schemas/runtime_bridge.py`: typed runtime handoff schema (`runtime.assignment.v1` + kernel model).
- `schemas/qube_kernel_bridge.py`: typed bridge schema for `chaos.test.receipt.v1` and AXIS receipt tokens.
- `tests/test_release_orchestrator.py`: release-control behavior tests.

## API Token Control
- `mcp_token.py`: sovereign token issuer for cross-agent Model Context Protocol handshake.
- `client_token_pipe.py`: high-throughput token provisioning for frontend/client workers.

## Forensic & Governance
- `judge/decision.py`: judge-model decision logic for release gating.
- `scripts/verification/verify_capsule_archive.py`: deterministic verification of frozen capsules.
