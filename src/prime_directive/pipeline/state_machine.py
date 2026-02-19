from __future__ import annotations

from enum import Enum


class PipelineState(str, Enum):
    IDLE = "idle"
    RENDERING = "rendering"
    VALIDATING = "validating"
    HALTED = "halted"
    EXPORTING = "exporting"
    COMMITTING = "committing"
    PASSED = "passed"
