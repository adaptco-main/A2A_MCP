from __future__ import annotations

from prime_directive.validators.common import GateResult


def validate_provenance(payload: dict) -> GateResult:
    return GateResult(name="provenance", passed=payload.get("provenance", True))
