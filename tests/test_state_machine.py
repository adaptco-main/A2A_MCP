from prime_directive.pipeline.context import PipelineContext
from prime_directive.pipeline.engine import PipelineEngine
from prime_directive.pipeline.state_machine import PipelineState


def test_engine_halts_when_gate_fails():
    engine = PipelineEngine()
    ctx = PipelineContext(run_id="r1", payload={}, gate_results={"preflight": False})
    assert engine.run(ctx) == PipelineState.HALTED
