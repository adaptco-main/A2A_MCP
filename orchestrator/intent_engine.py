from __future__ import annotations

import uuid
from typing import List

from agents.coder import CoderAgent
from agents.pinn_agent import PINNAgent
from agents.tester import TesterAgent
from schemas.agent_artifacts import MCPArtifact
from schemas.project_plan import ProjectPlan


class IntentEngine:
    """Executes project plans across coder/tester/PINN agents."""

    def __init__(self) -> None:
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        self.pinn = PINNAgent()
        # Reuse coder DB manager as shared persistence layer.
        self.db = self.coder.db

    async def execute_plan(self, plan: ProjectPlan) -> List[str]:
        artifact_ids: List[str] = []
        previous_code_artifact_id = plan.plan_id

        for action in plan.actions:
            action.status = "in_progress"

            code_artifact = await self.coder.generate_solution(
                parent_id=previous_code_artifact_id,
                feedback=action.instruction,
            )
            artifact_ids.append(code_artifact.artifact_id)
            self.db.save_artifact(code_artifact)

            report = await self.tester.validate(code_artifact.artifact_id)
            report_artifact = MCPArtifact(
                artifact_id=str(uuid.uuid4()),
                type="test_report",
                content=report.critique,
                metadata={"status": report.status, "action_id": action.action_id},
            )
            artifact_ids.append(report_artifact.artifact_id)
            self.db.save_artifact(report_artifact)

            pinn_token = self.pinn.ingest_artifact(
                artifact_id=code_artifact.artifact_id,
                content=code_artifact.content,
                parent_id=previous_code_artifact_id,
            )
            artifact_ids.append(pinn_token.token_id)

            if report.status == "PASS":
                action.status = "completed"
            else:
                action.status = "failed"
            action.validation_feedback = report.critique

            # Chain the *code* artifact between actions.
            previous_code_artifact_id = code_artifact.artifact_id

        return artifact_ids

    async def process_plan(self, plan: ProjectPlan) -> List[str]:
        """Backwards-compatible alias."""
        return await self.execute_plan(plan)
