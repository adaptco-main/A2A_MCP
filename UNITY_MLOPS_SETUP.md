# Unity MLOps Setup Guide

This guide shows how to run autonomous Unity + ML-Agents training with `mlops_unity_pipeline.py`.

## 1) Prerequisites

- Unity installed and available on PATH (or pass explicit executable path).
- Python 3.10+
- ML-Agents package:

```bash
pip install mlagents==1.0.0 pyyaml croniter
```

Optional integrations:

- `google-cloud-aiplatform` for Vertex AI model registration.
- `aiohttp` for webhook notifications from scheduled runs.

## 2) Quick Start (single job)

```python
import asyncio
from mlops_unity_pipeline import (
    UnityAssetSpec,
    RLTrainingConfig,
    TrainingJob,
    UnityMLOpsOrchestrator,
)


async def main() -> None:
    orchestrator = UnityMLOpsOrchestrator(dry_run=True)

    asset = UnityAssetSpec(
        asset_id="test-001",
        name="SimpleAgent",
        asset_type="behavior",
        description="Reach target position while avoiding obstacles.",
        observation_space={"raycast": 8, "velocity": 2},
        action_space={"type": "continuous", "size": 2},
    )

    config = RLTrainingConfig(
        algorithm="PPO",
        max_steps=100_000,
        num_envs=8,
        time_scale=20.0,
    )

    job = TrainingJob(
        job_id="test-job",
        asset_spec=asset,
        rl_config=config,
        unity_project_path="/path/to/unity/project",
        output_dir="artifacts",
    )

    result = await orchestrator.execute_training_job(job)
    print(result)


asyncio.run(main())
```

> Set `dry_run=False` to execute real Unity builds and ML-Agents training.

## 3) 24/7 Scheduled Training

```python
import asyncio
from mlops_unity_pipeline import (
    UnityAssetSpec,
    RLTrainingConfig,
    TrainingSchedule,
    TrainingScheduler,
    UnityMLOpsOrchestrator,
)


async def run_forever() -> None:
    orchestrator = UnityMLOpsOrchestrator(dry_run=True)
    scheduler = TrainingScheduler(orchestrator, max_concurrency=2)

    nightly_asset = UnityAssetSpec(
        asset_id="patrol-001",
        name="PatrolAgent",
        asset_type="behavior",
        description="Patrol between waypoints while avoiding obstacles.",
    )

    schedule = TrainingSchedule(
        schedule_id="nightly",
        cron_expression="0 2 * * *",  # 2 AM UTC daily
        asset_specs=[nightly_asset],
        rl_config=RLTrainingConfig(algorithm="PPO", max_steps=1_000_000),
        unity_project_path="/path/to/unity/project",
        output_dir="artifacts",
        webhook_url="https://example.com/webhook/training",
    )

    scheduler.add_schedule(schedule)
    await scheduler.run_forever()


asyncio.run(run_forever())
```

## 4) Offline RL Pattern

1. Collect demonstrations with ML-Agents tools.
2. Store `.demo` assets per behavior.
3. Enable offline-first config:
   - `use_offline_demonstrations=True`
   - `demonstration_path="/path/to/demo"`
4. Run training job as usual; pipeline passes initialization hint to trainer.

## 5) Vertex AI Registration

Set these fields on `TrainingJob`:

- `vertex_project`
- `vertex_region` (defaults to `us-central1`)
- Optional `vertex_model_display_name`

When configured, the pipeline uploads the trained artifact directory as a Vertex model.

## 6) Integration with Existing A2A-MCP Flow

- Keep current bridge/orchestrator components for intent → code generation.
- Use `UnityMLOpsOrchestrator` as the next stage for build/train/register.
- Persist generated artifacts under `artifacts/<job_id>/` for traceability.

## 7) Production Notes

- Use a dedicated Unity build machine or container image.
- Route training runs to GPU nodes.
- Store `artifacts/` in cloud object storage.
- Forward training logs to your observability stack.
- Wrap scheduler in a process manager (systemd/Kubernetes CronJob/Deployment).
