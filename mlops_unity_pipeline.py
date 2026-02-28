"""Autonomous Unity MLOps pipeline orchestration.

This module provides a production-friendly scaffold for generating Unity assets
from natural language, building Unity environments, training RL agents with
ML-Agents, and registering trained artifacts in Vertex AI.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import textwrap
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from croniter import croniter
from jsonschema import Draft202012Validator

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UnityAssetSpec:
    """Specification for a Unity asset/agent to generate."""

    asset_id: str
    name: str
    asset_type: str
    description: str
    observation_space: Dict[str, Any] = field(default_factory=dict)
    action_space: Dict[str, Any] = field(default_factory=dict)
    reward_spec: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)


@dataclass(slots=True)
class RLTrainingConfig:
    """Training configuration for ML-Agents jobs."""

    algorithm: str = "PPO"
    max_steps: int = 1_000_000
    num_envs: int = 16
    time_scale: float = 20.0
    batch_size: int = 1024
    learning_rate: float = 3.0e-4
    checkpoint_interval: int = 50_000
    use_offline_rl: bool = True
    demonstrations_path: Optional[str] = None


@dataclass(slots=True)
class TrainingJob:
    """A single end-to-end training unit."""

    job_id: str
    asset_spec: UnityAssetSpec
    rl_config: RLTrainingConfig
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class TrainingResult:
    """Result payload from a completed training pipeline."""

    job_id: str
    status: str
    generated_code_path: Optional[str] = None
    unity_build_path: Optional[str] = None
    trained_model_path: Optional[str] = None
    model_registry_uri: Optional[str] = None
    metrics_path: Optional[str] = None
    error: Optional[str] = None


@dataclass(slots=True)
class TrainingSchedule:
    """Cron-style schedule for recurring training jobs."""

    schedule_id: str
    cron_expression: str
    asset_specs: List[UnityAssetSpec]
    rl_config: RLTrainingConfig
    enabled: bool = True


@dataclass(slots=True)
class TransitionDecision:
    """Decision returned by control-plane transition checks."""

    allowed: bool
    reason: str


class ControlPlaneRuntime:
    """Minimal control-plane loop for API-surface exploration and guardrails.

    Contract:
    1) Load YAML bundle and enumerate `api_surface.tools[].actions[].id`
    2) Generate MCP stub tool list from action ids
    3) Compile JSON Schemas from `schemas/*` (fail-closed)
    4) Validate runtime tool inputs for every invocation
    5) Append immutable JSONL events
    6) Replay JSONL to compute state/derived facts
    7) Evaluate transition requirements
    8) Halt if guardrails/HITL are not satisfied
    """

    def __init__(
        self,
        bundle_path: str,
        schemas_dir: str,
        events_path: str,
    ) -> None:
        self.bundle_path = Path(bundle_path)
        self.schemas_dir = Path(schemas_dir)
        self.events_path = Path(events_path)
        self._append_lock = asyncio.Lock()
        self._validators: Dict[str, Draft202012Validator] = {}

    def load_bundle(self) -> Dict[str, Any]:
        """Load YAML bundle and return structured dict."""

        if not self.bundle_path.exists():
            raise FileNotFoundError(f"Bundle not found: {self.bundle_path}")

        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:  # pragma: no cover - import depends on environment
            raise RuntimeError("PyYAML is required to load YAML bundles") from exc

        parsed = yaml.safe_load(self.bundle_path.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            raise ValueError("YAML bundle must deserialize into a mapping")
        return parsed

    def enumerate_action_ids(self, bundle: Dict[str, Any]) -> List[str]:
        """Enumerate `api_surface.tools[*].actions[*].id` values."""

        action_ids: List[str] = []
        tools = bundle.get("api_surface", {}).get("tools", [])
        for tool in tools:
            for action in tool.get("actions", []):
                action_id = action.get("id")
                if isinstance(action_id, str) and action_id:
                    action_ids.append(action_id)
        if not action_ids:
            raise ValueError("No action IDs found in api_surface.tools[*].actions[*].id")
        return action_ids

    def generate_mcp_stub_tools(self, action_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate minimal MCP stub descriptors from action IDs."""

        return [
            {
                "name": action_id,
                "description": f"Stub MCP tool for action `{action_id}`",
                "inputSchema": {"type": "object", "additionalProperties": True},
            }
            for action_id in action_ids
        ]

    def compile_schemas(self) -> Dict[str, Draft202012Validator]:
        """Compile all JSON schemas in `schemas/*` and fail-closed if absent."""

        schema_files = sorted(self.schemas_dir.glob("*.json"))
        if not schema_files:
            raise FileNotFoundError(f"No schema files found in {self.schemas_dir}")

        validators: Dict[str, Draft202012Validator] = {}
        for schema_file in schema_files:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            validator = Draft202012Validator(schema)
            validators[schema_file.stem] = validator

        self._validators = validators
        return validators

    def validate_tool_input(self, action_id: str, payload: Dict[str, Any]) -> None:
        """Validate tool payload against compiled schema for action ID."""

        if not self._validators:
            raise RuntimeError("Schemas are not compiled; call compile_schemas() first")

        validator = self._validators.get(action_id)
        if validator is None:
            raise KeyError(f"Missing schema for action ID: {action_id}")

        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        if errors:
            details = "; ".join(error.message for error in errors)
            raise ValueError(f"Input validation failed for {action_id}: {details}")

    async def append_event(self, event: Dict[str, Any]) -> None:
        """Append an event to JSONL ledger using single-writer lock."""

        enriched_event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        self.events_path.parent.mkdir(parents=True, exist_ok=True)

        async with self._append_lock:
            with self.events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(enriched_event, sort_keys=True) + "\n")

    def replay_events(self) -> Dict[str, Any]:
        """Replay append-only JSONL to derive current control-plane state."""

        state: Dict[str, Any] = {
            "event_count": 0,
            "last_event_type": None,
            "tool_invocations": {},
            "guardrails_ok": True,
            "hitl_approved": False,
        }
        if not self.events_path.exists():
            return state

        for raw_line in self.events_path.read_text(encoding="utf-8").splitlines():
            if not raw_line.strip():
                continue
            event = json.loads(raw_line)
            state["event_count"] += 1
            state["last_event_type"] = event.get("event_type")

            action_id = event.get("action_id")
            if action_id:
                invocations = state["tool_invocations"]
                invocations[action_id] = invocations.get(action_id, 0) + 1

            if event.get("event_type") == "guardrail_violation":
                state["guardrails_ok"] = False
            if event.get("event_type") == "hitl_approval":
                state["hitl_approved"] = bool(event.get("approved", False))

        return state

    def evaluate_transition_requirements(
        self,
        requires: List[str],
        state: Dict[str, Any],
    ) -> TransitionDecision:
        """Evaluate `workflow.transitions[*].requires` against derived state."""

        missing = [requirement for requirement in requires if not bool(state.get(requirement))]
        if missing:
            return TransitionDecision(False, f"Missing required facts: {', '.join(missing)}")
        return TransitionDecision(True, "Requirements satisfied")

    def enforce_guardrails_and_hitl(
        self,
        decision: TransitionDecision,
        state: Dict[str, Any],
    ) -> TransitionDecision:
        """Allow transition only when requirements, guardrails, and HITL are satisfied."""

        if not decision.allowed:
            return decision
        if not state.get("guardrails_ok", False):
            return TransitionDecision(False, "Blocked/HALT: guardrail violation detected")
        if not state.get("hitl_approved", False):
            return TransitionDecision(False, "Blocked/HALT: missing HITL approval")
        return TransitionDecision(True, "Allow transition / continue")


class UnityMLOpsOrchestrator:
    """Executes generation, build, training, and registry stages."""

    def __init__(
        self,
        workspace: str = "./mlops_workspace",
        llm_endpoint: Optional[str] = None,
        vertex_project: Optional[str] = None,
        vertex_region: str = "us-central1",
    ) -> None:
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.llm_endpoint = llm_endpoint
        self.vertex_project = vertex_project
        self.vertex_region = vertex_region

    async def execute_training_job(self, job: TrainingJob) -> TrainingResult:
        """Run the full autonomous MLOps training pipeline."""

        logger.info("Starting training job %s", job.job_id)
        result = TrainingResult(job_id=job.job_id, status="running")

        try:
            code_path = await self.generate_unity_code(job)
            result.generated_code_path = str(code_path)

            build_path = await self.build_unity_environment(job, code_path)
            result.unity_build_path = str(build_path)

            model_path, metrics_path = await self.train_rl_agent(job, build_path)
            result.trained_model_path = str(model_path)
            result.metrics_path = str(metrics_path)

            registry_uri = await self.register_model(job, model_path)
            result.model_registry_uri = registry_uri
            result.status = "completed"
            logger.info("Training job %s completed successfully", job.job_id)
            return result

        except Exception as exc:  # noqa: BLE001 - surface pipeline failure in result
            logger.exception("Training job %s failed", job.job_id)
            result.status = "failed"
            result.error = str(exc)
            return result

    async def generate_unity_code(self, job: TrainingJob) -> Path:
        """Generate Unity C# behavior script from job spec."""

        job_dir = self._job_dir(job.job_id)
        code_dir = job_dir / "generated"
        code_dir.mkdir(parents=True, exist_ok=True)

        prompt = self._build_generation_prompt(job.asset_spec)
        script_contents = await self._invoke_llm(prompt, job.asset_spec)

        script_path = code_dir / f"{job.asset_spec.name}.cs"
        script_path.write_text(script_contents, encoding="utf-8")

        spec_path = code_dir / "asset_spec.json"
        spec_path.write_text(json.dumps(job.asset_spec.__dict__, indent=2), encoding="utf-8")

        return script_path

    async def build_unity_environment(self, job: TrainingJob, script_path: Path) -> Path:
        """Build headless Unity environment suitable for ML-Agents training."""

        build_dir = self._job_dir(job.job_id) / "build"
        build_dir.mkdir(parents=True, exist_ok=True)

        command = os.getenv("UNITY_BUILD_COMMAND")
        if command:
            await self._run_subprocess(command, cwd=str(build_dir))
        else:
            placeholder = build_dir / "README.txt"
            placeholder.write_text(
                "Set UNITY_BUILD_COMMAND to run headless Unity builds in production.",
                encoding="utf-8",
            )

        metadata = {
            "job_id": job.job_id,
            "source_script": str(script_path),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        (build_dir / "build_metadata.json").write_text(
            json.dumps(metadata, indent=2),
            encoding="utf-8",
        )
        return build_dir

    async def train_rl_agent(self, job: TrainingJob, build_path: Path) -> tuple[Path, Path]:
        """Train RL policy using ML-Agents (or placeholder local run)."""

        training_dir = self._job_dir(job.job_id) / "training"
        training_dir.mkdir(parents=True, exist_ok=True)

        config_path = training_dir / "training_config.yaml"
        config_path.write_text(self._to_mlagents_yaml(job.rl_config), encoding="utf-8")

        mlagents_cmd = os.getenv("MLAGENTS_TRAIN_COMMAND")
        if mlagents_cmd:
            await self._run_subprocess(mlagents_cmd, cwd=str(training_dir))

        model_path = training_dir / f"{job.asset_spec.name}.onnx"
        model_path.write_bytes(b"placeholder-model-bytes")

        metrics = {
            "algorithm": job.rl_config.algorithm,
            "max_steps": job.rl_config.max_steps,
            "num_envs": job.rl_config.num_envs,
            "offline_rl": job.rl_config.use_offline_rl,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "build_path": str(build_path),
        }
        metrics_path = training_dir / "metrics.json"
        metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        return model_path, metrics_path

    async def register_model(self, job: TrainingJob, model_path: Path) -> str:
        """Register model artifact in Vertex AI or local fallback registry."""

        if self.vertex_project:
            return (
                f"projects/{self.vertex_project}/locations/{self.vertex_region}/"
                f"models/{job.asset_spec.name}:{job.job_id}"
            )

        registry_dir = self.workspace / "registry"
        registry_dir.mkdir(parents=True, exist_ok=True)
        target = registry_dir / f"{job.asset_spec.name}-{job.job_id}.onnx"
        target.write_bytes(model_path.read_bytes())
        return f"file://{target.resolve()}"

    def _job_dir(self, job_id: str) -> Path:
        job_dir = self.workspace / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        return job_dir

    def _build_generation_prompt(self, asset_spec: UnityAssetSpec) -> str:
        return textwrap.dedent(
            f"""
            You are generating Unity ML-Agents C# behavior scripts.
            Asset name: {asset_spec.name}
            Asset type: {asset_spec.asset_type}
            Description:
            {asset_spec.description}

            Observation space: {json.dumps(asset_spec.observation_space, indent=2)}
            Action space: {json.dumps(asset_spec.action_space, indent=2)}
            Reward spec: {json.dumps(asset_spec.reward_spec or {}, indent=2)}

            Return only compilable C# code for a single MonoBehaviour/Agent script.
            """
        ).strip()

    async def _invoke_llm(self, prompt: str, asset_spec: UnityAssetSpec) -> str:
        # Integrate your provider SDK here (OpenAI, Vertex AI, etc.).
        _ = prompt
        await asyncio.sleep(0)
        return textwrap.dedent(
            f"""
            using Unity.MLAgents;
            using Unity.MLAgents.Actuators;
            using Unity.MLAgents.Sensors;
            using UnityEngine;

            public class {asset_spec.name} : Agent
            {{
                public override void OnEpisodeBegin() {{ }}

                public override void CollectObservations(VectorSensor sensor)
                {{
                    // TODO: implement observations based on asset spec.
                }}

                public override void OnActionReceived(ActionBuffers actions)
                {{
                    // TODO: implement action handling and reward logic.
                }}
            }}
            """
        ).strip() + "\n"

    async def _run_subprocess(self, command: str, cwd: Optional[str] = None) -> None:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(
                returncode=process.returncode,
                cmd=command,
                output=stdout,
                stderr=stderr,
            )

    def _to_mlagents_yaml(self, cfg: RLTrainingConfig) -> str:
        return textwrap.dedent(
            f"""
            behaviors:
              DefaultBehavior:
                trainer_type: {cfg.algorithm.lower()}
                hyperparameters:
                  batch_size: {cfg.batch_size}
                  learning_rate: {cfg.learning_rate}
                max_steps: {cfg.max_steps}
                time_horizon: 64
                summary_freq: {cfg.checkpoint_interval}
            env_settings:
              num_envs: {cfg.num_envs}
              time_scale: {cfg.time_scale}
            """
        ).strip() + "\n"


class TrainingScheduler:
    """Runs recurring autonomous training schedules."""

    def __init__(self, orchestrator: UnityMLOpsOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._schedules: Dict[str, TrainingSchedule] = {}
        self._stop_event = asyncio.Event()

    def add_schedule(self, schedule: TrainingSchedule) -> None:
        self._schedules[schedule.schedule_id] = schedule

    def remove_schedule(self, schedule_id: str) -> None:
        self._schedules.pop(schedule_id, None)

    async def run_forever(self, poll_interval_seconds: int = 30) -> None:
        logger.info("Starting scheduler with %d schedules", len(self._schedules))
        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc)
            due_schedules = [
                schedule
                for schedule in self._schedules.values()
                if schedule.enabled and self._is_due(schedule, now)
            ]

            if due_schedules:
                await asyncio.gather(*(self._run_schedule(schedule) for schedule in due_schedules))

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=poll_interval_seconds)
            except asyncio.TimeoutError:
                continue

    def stop(self) -> None:
        self._stop_event.set()

    async def _run_schedule(self, schedule: TrainingSchedule) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for asset_spec in schedule.asset_specs:
            job_id = f"{schedule.schedule_id}-{asset_spec.asset_id}-{timestamp}"
            job = TrainingJob(job_id=job_id, asset_spec=asset_spec, rl_config=schedule.rl_config)
            await self.orchestrator.execute_training_job(job)

    def _is_due(self, schedule: TrainingSchedule, now: datetime) -> bool:
        minute_start = now.replace(second=0, microsecond=0)
        previous_minute = minute_start.timestamp() - 60
        itr = croniter(schedule.cron_expression, previous_minute)
        due_time = datetime.fromtimestamp(float(itr.get_next()), tz=timezone.utc)
        return due_time == minute_start
