"""Validator interfaces and shared structures."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    """Result produced by a validation gate."""

    passed: bool
    message: str = ""
