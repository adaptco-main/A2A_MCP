"""Core pipeline coordinator for multi-agent orchestration."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Dict, List, Any

from agents.architecture_agent import ArchitectureAgent
from agents.coder import CoderAgent
from agents.managing_agent import ManagingAgent
from agents.orchestration_agent import OrchestrationAgent
from agents.pinn_agent import PINNAgent
from agents.tester import TesterAgent
from orchestrator.judge_orchestrator import get_judge_orchestrator
from orchestrator.notifier import (
    WhatsAppNotifier,
    send_pipeline_completion_notification,
)
from orchestrator.storage import DBManager
from orchestrator.vector_gate import VectorGate, VectorGateDecision
from schemas.agent_artifacts import MCPArtifact
from schemas.project_plan import ProjectPlan


@dataclass
class PipelineResult:
    """Typed output of a full 5-agent pipeline run."""

    plan: ProjectPlan
    blueprint: ProjectPlan
    architecture_artifacts: List[MCPArtifact] = field(default_factory=list)
    code_artifacts: List[MCPArtifact] = field(default_factory=list)
    test_verdicts: List[Dict[str, str]] = field(default_factory=list)
    success: bool = False


class IntentEngine:
    """Coordinates multi-agent execution across the full swarm."""

    _logger = logging.getLogger("IntentEngine")

    def __init__(self) -> None:
        self.manager = ManagingAgent()
        self.orchestrator = OrchestrationAgent()
        self.architect = ArchitectureAgent()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        self.pinn = PINNAgent()
        self.judge = get_judge_orchestrator()
        self.whatsapp_notifier = WhatsAppNotifier.from_env()
        self.vector_gate = VectorGate()
        self.db = DBManager()

        # RBAC integration (optional, gracefully degrades)
        self._rbac_enabled = os.getenv("RBAC_ENABLED", "true").lower() == "true"
        self._rbac_client = None
        if self._rbac_enabled:
            try:
                from rbac.client import RBACClient
                rbac_url = os.getenv("RBAC_URL", "http://rbac-gateway:8001")
                self._rbac_client = RBACClient(rbac_url)
            except ImportError:
                self._logger.warning("rbac package not installed — RBAC disabled.")

    async def run_full_pipeline(
        self,
        description: str,
        requester: str = "system",
        max_healing_retries: int = 3,
    ) -> PipelineResult:
        """
        End-to-end orchestration:

        1. **ManagingAgent** — categorise *description* into PlanActions.
        2. **OrchestrationAgent** — build a typed blueprint with delegation.
        3. **ArchitectureAgent** — map system architecture + WorldModel.
        4. **CoderAgent** — generate code artifacts for each action.
        5. **TesterAgent** — validate artifacts; self-heal on failure.

        Returns a ``PipelineResult`` with all intermediary artefacts.
        """
        # ── RBAC gate ───────────────────────────────────────────────
        if self._rbac_client and self._rbac_enabled:
            if not self._rbac_client.verify_permission(requester, action="run_pipeline"):
                raise PermissionError(
                    f"Agent '{requester}' is not permitted to run the pipeline. "
                    f"Onboard the agent with role 'pipeline_operator' or 'admin' first."
                )
            self._logger.info("RBAC: '%s' authorized for run_pipeline.", requester)

        result = PipelineResult(
            plan=ProjectPlan(
                plan_id="pending",
                project_name=description[:80],
                requester=requester,
            ),
            blueprint=ProjectPlan(
                plan_id="pending",
                project_name=description[:80],
                requester=requester,
            ),
        )

        plan = await self.manager.categorize_project(description, requester)
        result.plan = plan

        task_descriptions = [a.instruction for a in plan.actions]
        blueprint = await self.orchestrator.build_blueprint(
            project_name=plan.project_name,
            task_descriptions=task_descriptions,
            requester=requester,
        )
        result.blueprint = blueprint

        arch_artifacts = await self.architect.map_system(blueprint)
        result.architecture_artifacts = arch_artifacts
        last_code_artifact_id: str | None = None
        for action in blueprint.actions:
            action.status = "in_progress"
            parent_id = last_code_artifact_id or blueprint.plan_id

            coder_context = self.judge.get_agent_system_context("CoderAgent")
            coder_gate = self.vector_gate.evaluate(
                node="coder_input",
                query=f"{action.title}\n{action.instruction}",
                world_model=self.architect.pinn.world_model,
            )
            coder_vector_context = self.vector_gate.format_prompt_context(coder_gate)
            coding_task = (
                f"{coder_context}\n\n"
                f"{coder_vector_context}\n\n"
                "Implement this task with tests and safety checks:\n"
                f"{action.instruction}"
            )
            
            artifact = await self._generate_with_gate(
                parent_id=parent_id,
                feedback=coding_task,
                context_tokens=coder_gate.matches,
            )
            self._attach_gate_metadata(artifact, coder_gate)
            # CoderAgent usually persists, but we ensure it's saved if needed
            if not self.db.get_artifact(artifact.artifact_id):
                self.db.save_artifact(artifact)
            
            last_code_artifact_id = artifact.artifact_id

            healed = False
            for attempt in range(max_healing_retries):
                tester_gate = self.vector_gate.evaluate(
                    node="tester_input",
                    query=f"{action.instruction}\n{getattr(artifact, 'content', '')}",
                    world_model=self.architect.pinn.world_model,
                )
                tester_context = self.vector_gate.format_prompt_context(tester_gate)
                report = await self._validate_with_gate(
                    artifact_id=artifact.artifact_id,
                    supplemental_context=tester_context,
                    context_tokens=tester_gate.matches,
                )
                judgment = self.judge.judge_action(
                    action=(
                        f"TesterAgent verdict for {artifact.artifact_id}: "
                        f"{report.status}"
                    ),
                    context={
                        "attempt": attempt + 1,
                        "max_retries": max_healing_retries,
                        "artifact_id": artifact.artifact_id,
                    },
                    agent_name="TesterAgent",
                )
                result.test_verdicts.append(
                    {
                        "artifact": artifact.artifact_id,
                        "status": report.status,
                        "vector_gate": "open" if tester_gate.is_open else "closed",
                        "judge_score": f"{judgment.overall_score:.3f}",
                    }
                )

                if report.status == "PASS":
                    healed = True
                    break

                refine_context = self.judge.get_agent_system_context("CoderAgent")
                healing_gate = self.vector_gate.evaluate(
                    node="healing_input",
                    query=f"{action.instruction}\n{report.critique}",
                    world_model=self.architect.pinn.world_model,
                )
                healing_vector_context = self.vector_gate.format_prompt_context(healing_gate)
                artifact = await self._generate_with_gate(
                    parent_id=artifact.artifact_id,
                    feedback=(
                        f"{refine_context}\n\n"
                        f"{healing_vector_context}\n\n"
                        f"Tester feedback:\n{report.critique}"
                    ),
                    context_tokens=healing_gate.matches,
                )
                self._attach_gate_metadata(artifact, healing_gate)
                if not self.db.get_artifact(artifact.artifact_id):
                    self.db.save_artifact(artifact)

            result.code_artifacts.append(artifact)
            last_code_artifact_id = artifact.artifact_id
            action.status = "completed" if healed else "failed"

        result.success = all(a.status == "completed" for a in blueprint.actions)
        completed_actions = sum(1 for action in blueprint.actions if action.status == "completed")
        failed_actions = sum(1 for action in blueprint.actions if action.status == "failed")
        self._notify_completion(
            project_name=blueprint.project_name,
            success=result.success,
            completed_actions=completed_actions,
            failed_actions=failed_actions,
        )
        return result

    async def execute_plan(self, plan: ProjectPlan) -> List[str]:
        """Legacy action-level coder->tester loop for backward compatibility."""
        artifact_ids: List[str] = []
        last_code_artifact_id: str | None = None

        for action in plan.actions:
            action.status = "in_progress"
            parent_id = last_code_artifact_id or plan.plan_id

            coder_gate = self.vector_gate.evaluate(
                node="legacy_coder_input",
                query=f"{action.title}\n{action.instruction}",
                world_model=self.architect.pinn.world_model,
            )
            coder_vector_context = self.vector_gate.format_prompt_context(coder_gate)
            
            artifact = await self._generate_with_gate(
                parent_id=parent_id,
                feedback=f"{coder_vector_context}\n\n{action.instruction}",
                context_tokens=coder_gate.matches,
            )
            self._attach_gate_metadata(artifact, coder_gate)
            if not self.db.get_artifact(artifact.artifact_id):
                self.db.save_artifact(artifact)
            
            artifact_ids.append(artifact.artifact_id)
            last_code_artifact_id = artifact.artifact_id

            # Validate with Tester
            tester_gate = self.vector_gate.evaluate(
                node="legacy_tester_input",
                query=f"{action.instruction}\n{getattr(artifact, 'content', '')}",
                world_model=self.architect.pinn.world_model,
            )
            tester_context = self.vector_gate.format_prompt_context(tester_gate)
            report = await self._validate_with_gate(
                artifact_id=artifact.artifact_id,
                supplemental_context=tester_context,
                context_tokens=tester_gate.matches,
            )
            
            # Save Test Report
            test_artifact_id = str(uuid.uuid4())
            report_artifact = SimpleNamespace(
                artifact_id=test_artifact_id,
                parent_artifact_id=artifact.artifact_id,
                agent_name=self.tester.agent_name,
                version="1.0.0",
                type="test_report",
                content=report.model_dump_json() if hasattr(report, 'model_dump_json') else str(report),
            )
            # Minimal metadata for DBManager.save_artifact compatibility
            if not hasattr(report_artifact, "metadata"):
                report_artifact.metadata = {}
            
            self.db.save_artifact(report_artifact)
            artifact_ids.append(test_artifact_id)

            action.status = "completed" if report.status == "PASS" else "failed"

        self._notify_completion(
            project_name=plan.project_name,
            success=all(a.status == "completed" for a in plan.actions),
            completed_actions=sum(1 for a in plan.actions if a.status == "completed"),
            failed_actions=sum(1 for a in plan.actions if a.status == "failed"),
        )
        return artifact_ids

    def _notify_completion(
        self,
        *,
        project_name: str,
        success: bool,
        completed_actions: int,
        failed_actions: int,
    ) -> None:
        """Send best-effort completion notification without breaking execution."""
        try:
            send_pipeline_completion_notification(
                self.whatsapp_notifier,
                project_name=project_name,
                success=success,
                completed_actions=completed_actions,
                failed_actions=failed_actions,
            )
        except Exception:
            # Notifications are out-of-band and must never break task execution.
            pass

    async def _validate_with_gate(
        self,
        artifact_id: str,
        supplemental_context: str,
        context_tokens,
    ):
        """Validate artifacts with vector context when supported."""
        try:
            return await self.tester.validate(
                artifact_id,
                supplemental_context=supplemental_context,
                context_tokens=context_tokens,
            )
        except TypeError:
            try:
                return await self.tester.validate(
                    artifact_id,
                    supplemental_context=supplemental_context,
                )
            except TypeError:
                return await self.tester.validate(artifact_id)

    async def _generate_with_gate(self, parent_id: str, feedback: str, context_tokens):
        """Generate artifacts with token context when supported."""
        try:
            return await self.coder.generate_solution(
                parent_id=parent_id,
                feedback=feedback,
                context_tokens=context_tokens,
            )
        except TypeError:
            return await self.coder.generate_solution(
                parent_id=parent_id,
                feedback=feedback,
            )

    @staticmethod
    def _attach_gate_metadata(artifact: object, decision: VectorGateDecision) -> None:
        """Attach gate provenance to artifacts that expose a metadata attribute."""
        if not hasattr(artifact, "metadata"):
            return

        metadata = getattr(artifact, "metadata") or {}
        metadata["vector_gate"] = {
            "node": decision.node,
            "is_open": decision.is_open,
            "threshold": decision.threshold,
            "top_score": decision.top_score,
            "match_count": len(decision.matches),
            "matched_token_ids": [m.token_id for m in decision.matches],
        }
        setattr(artifact, "metadata", metadata)
