from __future__ import annotations

from prime_directive.validators.common import GateResult


def validate_preflight(payload: dict) -> GateResult:
    return GateResult(name="preflight", passed=bool(payload))
