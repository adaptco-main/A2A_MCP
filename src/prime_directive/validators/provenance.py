"""Provenance validation gate."""

from __future__ import annotations

from typing import Any

from prime_directive.validators.common import GateResult


def validate_provenance(payload: dict[str, Any]) -> GateResult:
    """Validate that payload provenance is explicitly boolean and truthy.

    Non-boolean provenance values are treated as invalid to avoid accidental
    truthiness bypasses (for example, the string ``"false"``).
    """

    provenance = payload.get("provenance", True)
    if not isinstance(provenance, bool):
        return GateResult(
            passed=False,
            message="provenance must be a boolean value",
        )

    if not provenance:
        return GateResult(passed=False, message="provenance validation failed")

    return GateResult(passed=True)
