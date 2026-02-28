# Unity Autonomous MLOps Setup

This guide documents the complete autonomous Unity training factory built around `mlops_unity_pipeline.py`.

## 🎯 What This Pipeline Automates

1. Generate Unity C# behavior scripts from natural language.
2. Build Unity environments in headless mode.
3. Train ML-Agents policies continuously (offline-first + online fine-tuning).
4. Register artifacts in Vertex AI.
5. Schedule recurring jobs (hourly/nightly/continuous).

```text
User Prompt ("Create a patrol AI")
        ↓
LLM Unity C# Generation
        ↓
Headless Unity Build
        ↓
ML-Agents Training (GPU / Offline RL)
        ↓
Vertex AI Model Registry
        ↓
Game Deployment (ONNX/Barracuda)
```

## Core Components

### `UnityAssetSpec`
Defines the behavior/environment asset to generate.

### `RLTrainingConfig`
Defines algorithm and training hyperparameters (PPO defaults included).

### `UnityMLOpsOrchestrator`
Executes full job lifecycle:
- `generate_unity_code`
- `build_unity_environment`
- `train_with_mlagents`
- `register_in_vertex_ai`

### `TrainingScheduler`
Cron-style automation with concurrency control and webhook notifications.

## 15-Minute Quick Start

### 1) Install Dependencies

```bash
pip install mlagents==1.0.0 pyyaml croniter
```

Optional:

```bash
pip install google-cloud-aiplatform aiohttp
```

### 2) Single Job Smoke Test

```python
import asyncio
from mlops_unity_pipeline import *


async def main():
    orchestrator = UnityMLOpsOrchestrator(dry_run=True)

    asset = UnityAssetSpec(
        asset_id="test-001",
        name="SimpleAgent",
        asset_type="behavior",
        description="Reach target position while avoiding obstacles.",
        observation_space={"raycast": 8, "velocity": 2},
        action_space={"type": "continuous", "size": 2},
    )

    cfg = RLTrainingConfig(
        algorithm="PPO",
        max_steps=100_000,
        num_envs=8,
        time_scale=20.0,
    )

    job = TrainingJob(job_id="test-job", asset_spec=asset, rl_config=cfg)
    result = await orchestrator.execute_training_job(job)
    print(f"✅ Complete! Model: {result.trained_model_path}")


asyncio.run(main())
```

> Set `dry_run=False` for real Unity builds and ML-Agents training.

### 3) 24/7 Scheduled Runs

```python
import asyncio
from mlops_unity_pipeline import *


async def run_forever():
    orchestrator = UnityMLOpsOrchestrator(dry_run=True)
    scheduler = TrainingScheduler(orchestrator)

    schedule = TrainingSchedule(
        schedule_id="nightly",
        cron_expression="0 2 * * *",  # 2AM UTC daily
        asset_specs=[
            UnityAssetSpec(
                asset_id="patrol-001",
                name="PatrolAgent",
                asset_type="behavior",
                description="Patrol between waypoints while avoiding obstacles.",
            )
        ],
        rl_config=RLTrainingConfig(algorithm="PPO", max_steps=1_000_000),
    )

    scheduler.add_schedule(schedule)
    await scheduler.run_forever()


asyncio.run(run_forever())
```

## Offline RL Workflow (Simple)

1. Record demonstrations once (`.demo` files).
2. Train from demonstrations without running the game continuously.
3. Optionally fine-tune online with live simulation.

Enable offline-first runs via `RLTrainingConfig`:

```python
RLTrainingConfig(
    use_offline_demonstrations=True,
    demonstration_path="/path/to/recorded.demo",
)
```

## Integration with Existing A2A-MCP Bridge

The Unity MLOps stage extends existing orchestration:

- Existing bridge handles intent → research → code planning.
- Unity MLOps handles build → RL train → model registration.

This keeps responsibilities clean while enabling end-to-end autonomous game AI generation.

## Production Deployment Notes

- Run Unity build workers in dedicated headless environments.
- Route ML-Agents jobs to GPU nodes.
- Persist `artifacts/<job_id>/` in durable object storage.
- Track experiments with TensorBoard.
- Run scheduler as Kubernetes Deployment / CronJob.
- Use webhook notifications for training status and failures.

## Suggested Adoption Plan

### Today
- Run single job smoke test in `dry_run` mode.
- Validate generated C# and output artifact folders.

### This Week
- Add real Unity build step (`dry_run=False`).
- Collect demonstration data for at least one gameplay behavior.
- Launch nightly schedule.

### This Month
- Enable Vertex AI model registration.
- Deploy trained ONNX models to runtime (Barracuda).
- Scale to multiple behaviors with concurrent schedules.
