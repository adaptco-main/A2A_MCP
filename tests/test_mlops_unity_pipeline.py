import asyncio
import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta, timezone

# Dynamic import to support local execution environments
module_path = Path(__file__).resolve().parents[1] / 'mlops_unity_pipeline.py'
spec = importlib.util.spec_from_file_location('mlops_unity_pipeline', module_path)
mlops = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules['mlops_unity_pipeline'] = mlops
spec.loader.exec_module(mlops)

RLTrainingConfig = mlops.RLTrainingConfig
TrainingJob = mlops.TrainingJob
UnityAssetSpec = mlops.UnityAssetSpec
UnityMLOpsOrchestrator = mlops.UnityMLOpsOrchestrator
TrainingSchedule = getattr(mlops, 'TrainingSchedule', None)
TrainingScheduler = getattr(mlops, 'TrainingScheduler', None)


def test_offline_training_writes_dataset_path() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        dataset = tmp_path / "demo.jsonl"
        dataset.write_text("{}\n", encoding="utf-8")

        orchestrator = UnityMLOpsOrchestrator()
        job = TrainingJob(
            job_id="offline-job",
            asset_spec=UnityAssetSpec(
                asset_id="a1",
                name="OfflineAgent",
                asset_type="behavior",
                description="Train from demonstrations",
            ),
            rl_config=RLTrainingConfig(
                training_mode="offline",
                offline_dataset_path=str(dataset),
            ),
            output_dir=str(tmp_path / "out"),
            register_to_vertex=False,
        )

        result = asyncio.run(orchestrator.execute_training_job(job))

        assert result.status == "completed"
        summary_path = Path(result.trained_model_path) / "training_summary.json"
        summary_text = summary_path.read_text(encoding="utf-8")
        assert '"training_mode": "offline"' in summary_text
        assert str(dataset.resolve()) in summary_text


def test_offline_training_requires_dataset() -> None:
    with TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        orchestrator = UnityMLOpsOrchestrator()
        job = TrainingJob(
            job_id="missing-dataset-job",
            asset_spec=UnityAssetSpec(
                asset_id="a2",
                name="MissingDatasetAgent",
                asset_type="behavior",
                description="Should fail without dataset",
            ),
            rl_config=RLTrainingConfig(training_mode="offline"),
            output_dir=str(tmp_path / "out"),
            register_to_vertex=False,
        )

        result = asyncio.run(orchestrator.execute_training_job(job))

        assert result.status == "failed"
        assert "offline_dataset_path is required" in (result.error or "")


def _schedule() -> TrainingSchedule:
    return TrainingSchedule(
        schedule_id="nightly-training",
        cron_expression="0 2 * * *",
        asset_specs=[
            UnityAssetSpec(
                asset_id="asset-001",
                name="PatrolAgent",
                asset_type="behavior",
                description="Patrol between waypoints",
            )
        ],
        rl_config=RLTrainingConfig(),
    )


def test_is_due_runs_immediately_when_no_checkpoint(tmp_path, monkeypatch):
    if not TrainingScheduler: return
    monkeypatch.chdir(tmp_path)
    scheduler = TrainingScheduler(UnityMLOpsOrchestrator())
    schedule = _schedule()

    now = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)

    assert scheduler._is_due(schedule, now) is True


def test_is_due_respects_checkpoint_after_first_run(tmp_path, monkeypatch):
    if not TrainingScheduler: return
    monkeypatch.chdir(tmp_path)
    scheduler = TrainingScheduler(UnityMLOpsOrchestrator())
    schedule = _schedule()

    now = datetime(2026, 1, 5, 12, 0, tzinfo=timezone.utc)
    assert scheduler._is_due(schedule, now) is True

    before_next_cron = now + timedelta(hours=1)
    assert scheduler._is_due(schedule, before_next_cron) is False
