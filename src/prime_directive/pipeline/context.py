from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PipelineContext:
    run_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    gate_results: dict[str, bool] = field(default_factory=dict)
    staging_root: Path = field(default_factory=lambda: Path("staging"))
    export_root: Path = field(default_factory=lambda: Path("exports"))
