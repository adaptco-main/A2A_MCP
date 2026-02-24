from __future__ import annotations

from prime_directive.pipeline.context import PipelineContext


class PipelineEngine:
    """Placeholder orchestration engine for staged migration."""

    def __init__(self) -> None:
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
