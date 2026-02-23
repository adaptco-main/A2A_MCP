from __future__ import annotations

from prime_directive.validators.common import GateResult


def validate_c5_geometry(payload: dict) -> GateResult:
    return GateResult(name="c5", passed="geometry" in payload)
