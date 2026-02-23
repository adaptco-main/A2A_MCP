from __future__ import annotations

from prime_directive.pipeline.context import PipelineContext
from prime_directive.pipeline.state_machine import PipelineState


class PipelineEngine:
    """Placeholder orchestration engine for staged migration."""

<<<<<<< ours
    def __init__(self, context: PipelineContext | None = None) -> None:
        self.context = context
=======
    def __init__(self) -> None:
>>>>>>> theirs
        self.state = PipelineState.IDLE

    def get_state(self) -> PipelineState:
        return self.state

    def run(self, ctx: PipelineContext) -> PipelineState:
        self.context = ctx
        self.state = PipelineState.RENDERED
        self.state = PipelineState.VALIDATED

        gate_results = getattr(ctx, "gate_results", None)
        if not gate_results or not all(gate_results.values()):
            self.state = PipelineState.HALTED
            return self.state

        self.state = PipelineState.EXPORTED
        self.state = PipelineState.COMMITTED
        return self.state
