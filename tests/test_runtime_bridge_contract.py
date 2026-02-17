from schemas.runtime_bridge import RuntimeAssignmentV1, RuntimeWorkerAssignment


def test_runtime_assignment_v1_round_trip():
    worker = RuntimeWorkerAssignment(
        worker_id="worker-01-runtime",
        agent_name="GameRuntimeAgent",
        role="runtime",
        fidelity="low",
        runtime_target="threejs_compact_worker",
        deployment_mode="compact_runtime",
        render_backend="threejs",
        runtime_shell="wasm",
        mcp={"provider": "github-mcp"},
    )
    assignment = RuntimeAssignmentV1(
        assignment_id="rtassign-abc123",
        handshake_id="hs-abc123",
        plan_id="plan-abc123",
        repository="adaptco/A2A_MCP",
        commit_sha="abc123",
        actor="qa_user",
        prompt="deploy runtime worker",
        runtime={"wasm_shell": {"enabled": True}},
        workers=[worker],
        token_stream=[{"token": "runtime", "token_id": "tok-1"}],
        mcp={"provider": "github-mcp", "api_key_fingerprint": "deadbeefdeadbeef"},
    )

    dumped = assignment.model_dump(mode="json")
    reparsed = RuntimeAssignmentV1.model_validate(dumped)

    assert reparsed.schema_version == "runtime.assignment.v1"
    assert reparsed.workers[0].render_backend == "threejs"
