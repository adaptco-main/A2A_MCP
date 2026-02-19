from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineContext:
    run_id: str
    payload: dict[str, Any]
    gate_results: dict[str, bool] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
