from __future__ import annotations

import unittest

from app.orchestrator_agent import (
    DependencyError,
    InvalidTransitionError,
    QubeWorkflowAgent,
    TaskStatus,
    WorkflowEvent,
    WorkflowTask,
)


class QubeWorkflowAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks = [
            WorkflowTask(id="alpha", title="Alpha"),
            WorkflowTask(id="beta", title="Beta", depends_on=("alpha",)),
            WorkflowTask(id="gamma", title="Gamma", depends_on=("beta",)),
        ]
        self.agent = QubeWorkflowAgent(self.tasks, name="Qube Integration")

    def test_ready_tasks_progress_with_dependency_completion(self) -> None:
        ready_ids = [task.id for task in self.agent.ready_tasks()]
        self.assertEqual(ready_ids, ["alpha"])

        self.agent.start_task("alpha", actor="ops")
        self.agent.complete_task("alpha", actor="ops")

        ready_ids = [task.id for task in self.agent.ready_tasks()]
        self.assertEqual(ready_ids, ["beta"])

    def test_start_requires_dependencies(self) -> None:
        with self.assertRaises(DependencyError):
            self.agent.start_task("beta", actor="ops")

    def test_start_and_complete_record_events(self) -> None:
        start_event = self.agent.start_task("alpha", actor="ops", notes="kickoff", assignee="ops")
        self.assertEqual(start_event.action, "start")

        complete_event = self.agent.complete_task(
            "alpha",
            actor="ops",
            notes="delivered",
            deliverables=("report.md",),
        )

        history = self.agent.history("alpha")
        self.assertEqual([event.action for event in history], ["start", "complete"])
        self.assertEqual(history[0].details.get("assignee"), "ops")
        self.assertEqual(history[1].details.get("deliverables"), ("report.md",))
        self.assertEqual(self.agent.task_status("alpha"), TaskStatus.COMPLETED)

    def test_block_and_unblock(self) -> None:
        block_event = self.agent.block_task("beta", actor="ops", reason="waiting on dependency")
        self.assertEqual(block_event.action, "block")
        self.assertEqual(self.agent.task_status("beta"), TaskStatus.BLOCKED)

        with self.assertRaises(InvalidTransitionError):
            self.agent.start_task("beta", actor="ops")

        unblock_event = self.agent.unblock_task("beta", actor="ops")
        self.assertEqual(unblock_event.action, "unblock")
        self.assertEqual(self.agent.task_status("beta"), TaskStatus.PENDING)

    def test_reset_returns_task_to_pending(self) -> None:
        self.agent.start_task("alpha", actor="ops")
        self.agent.complete_task("alpha", actor="ops")
        reset_event = self.agent.reset_task("alpha", actor="ops", reason="spec update")
        self.assertEqual(reset_event.action, "reset")
        self.assertEqual(self.agent.task_status("alpha"), TaskStatus.PENDING)

    def test_status_summary(self) -> None:
        summary = self.agent.status_summary()
        self.assertEqual(summary["name"], "Qube Integration")
        self.assertEqual(summary["counts"][TaskStatus.PENDING.value], 3)
        self.assertEqual(summary["ready"], ["alpha"])

    def test_generate_plan_respects_dependencies(self) -> None:
        order = [task.id for task in self.agent.tasks()]
        self.assertEqual(order, ["alpha", "beta", "gamma"])

    def test_history_returns_copy(self) -> None:
        self.agent.start_task("alpha", actor="ops")
        log = self.agent.history("alpha")
        self.assertIsInstance(log[0], WorkflowEvent)
        self.assertEqual(log[0].task_id, "alpha")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
