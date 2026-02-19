from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateResult:
    name: str
    passed: bool
    reason: str = ""
