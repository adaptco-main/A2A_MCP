from __future__ import annotations

from prime_directive.validators.common import GateResult


def validate_rsm_color(payload: dict) -> GateResult:
    return GateResult(name="rsm", passed="color_profile" in payload)
