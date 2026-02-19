from __future__ import annotations

from prime_directive.pipeline.context import PipelineContext
from prime_directive.pipeline.state_machine import PipelineState


class PipelineEngine:
    """Thin deterministic orchestrator skeleton.

    Full integration should wire render/validate/export/commit adapters incrementally.
    """

    def __init__(self) -> None:
        self.state = PipelineState.IDLE

    def get_state(self) -> PipelineState:
        return self.state

    def run(self, ctx: PipelineContext) -> PipelineState:
        self.state = PipelineState.RENDERING
        self.state = PipelineState.VALIDATING
        if not all(ctx.gate_results.values()):
            self.state = PipelineState.HALTED
            return self.state
        self.state = PipelineState.EXPORTING
        self.state = PipelineState.COMMITTING
        self.state = PipelineState.PASSED
        return self.state
