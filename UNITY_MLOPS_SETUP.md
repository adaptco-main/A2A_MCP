# Unity MLOps Pipeline Setup Guide

This guide explains how to use `mlops_unity_pipeline.py` to run an autonomous Unity → RL training → model registry workflow.

## What this pipeline does

1. Generate Unity C# behavior code from an asset description.
2. Build a headless Unity environment.
3. Train RL agents with ML-Agents (supports offline-first workflows).
4. Register model artifacts (Vertex AI URI if configured, file registry fallback if not).
5. Optionally run recurring schedules via cron expressions.

## Prerequisites

- Python 3.10+
- Unity project with ML-Agents package installed
- ML-Agents Python package (`mlagents`)
- `croniter`
- Optional: GCP Vertex AI project for registry integration

```bash
pip install mlagents==1.0.0 croniter pyyaml
```

## Quick start

```python
import asyncio
from mlops_unity_pipeline import (
    RLTrainingConfig,
    TrainingJob,
    UnityAssetSpec,
    UnityMLOpsOrchestrator,
)

async def main():
    orchestrator = UnityMLOpsOrchestrator()

    asset = UnityAssetSpec(
        asset_id="test-001",
        name="SimpleAgent",
        asset_type="behavior",
        description="Reach target position while avoiding obstacles",
        observation_space={"raycast": 8, "velocity": 2},
        action_space={"type": "continuous", "size": 2},
    )

    config = RLTrainingConfig(
        algorithm="PPO",
        max_steps=100_000,
        num_envs=8,
        time_scale=20.0,
    )

    job = TrainingJob(job_id="smoke-test-job", asset_spec=asset, rl_config=config)
    result = await orchestrator.execute_training_job(job)
    print(result)

asyncio.run(main())
```

## Environment variables

Use these to wire real build/train commands:

- `UNITY_BUILD_COMMAND`: command to build Unity in headless mode.
- `MLAGENTS_TRAIN_COMMAND`: command to run `mlagents-learn`.

Example:

```bash
export UNITY_BUILD_COMMAND='unity -batchmode -quit -projectPath /workspace/MyUnityGame -executeMethod BuildScript.PerformBuild'
export MLAGENTS_TRAIN_COMMAND='mlagents-learn training_config.yaml --run-id nightly --force'
```

## Scheduling jobs (24/7)

```python
import asyncio
from mlops_unity_pipeline import (
    RLTrainingConfig,
    TrainingSchedule,
    TrainingScheduler,
    UnityAssetSpec,
    UnityMLOpsOrchestrator,
)

async def run_forever():
    orchestrator = UnityMLOpsOrchestrator()
    scheduler = TrainingScheduler(orchestrator)

    schedule = TrainingSchedule(
        schedule_id="nightly",
        cron_expression="0 2 * * *",
        asset_specs=[
            UnityAssetSpec(
                asset_id="patrol-001",
                name="PatrolAgent",
                asset_type="behavior",
                description="Patrol between waypoints and avoid collisions",
            )
        ],
        rl_config=RLTrainingConfig(algorithm="PPO", max_steps=2_000_000, num_envs=16),
    )

    scheduler.add_schedule(schedule)
    await scheduler.run_forever()

asyncio.run(run_forever())
```

## Minimal control-plane API surface loop

`ControlPlaneRuntime` in `mlops_unity_pipeline.py` implements a fail-closed control-plane loop:

1. Load YAML bundle and parse `api_surface.tools[].actions[].id`.
2. Generate MCP stub tool descriptors for those action IDs.
3. Compile JSON Schemas from `schemas/*.json` (fails closed if missing).
4. Validate every tool invocation payload.
5. Persist append-only JSONL events.
6. Replay JSONL to derive current state facts.
7. Evaluate transition requirements (`workflow.transitions[*].requires`).
8. Block/HALT if guardrails fail or HITL approval is absent.

Example sketch:

```python
runtime = ControlPlaneRuntime(
    bundle_path="bundle.yaml",
    schemas_dir="schemas",
    events_path="runtime/events.jsonl",
)

bundle = runtime.load_bundle()
action_ids = runtime.enumerate_action_ids(bundle)
stubs = runtime.generate_mcp_stub_tools(action_ids)
_ = stubs

runtime.compile_schemas()
runtime.validate_tool_input("tool_action", {"example": "payload"})

await runtime.append_event({"event_type": "tool_invocation", "action_id": "tool_action"})
state = runtime.replay_events()
decision = runtime.evaluate_transition_requirements(["guardrails_ok"], state)
decision = runtime.enforce_guardrails_and_hitl(decision, state)
print(decision)
```

## Offline RL workflow

1. Collect demonstration trajectories from human/expert play.
2. Configure `RLTrainingConfig(use_offline_rl=True, demonstrations_path="...")`.
3. Run training to bootstrap from demonstrations.
4. Optionally fine-tune with additional online rollouts.

## Vertex AI model registration

Instantiate orchestrator with `vertex_project`:

```python
orchestrator = UnityMLOpsOrchestrator(
    vertex_project="my-gcp-project",
    vertex_region="us-central1",
)
```

The pipeline returns a Vertex-style model URI string when configured.

## Observability and operations

- Persist `metrics.json` from each job into dashboards.
- Send webhook events from `execute_training_job` wrapper code.
- Keep artifact directories (`generated/`, `build/`, `training/`) in durable storage.
- Use containerized workers (Docker/Kubernetes) for reproducible GPU scheduling.
