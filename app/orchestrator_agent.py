from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised when PyYAML is absent
    yaml = None


class WorkflowAgentError(RuntimeError):
    """Base exception for workflow orchestration failures."""


class TaskNotFoundError(WorkflowAgentError):
    """Raised when a requested task is not part of the workflow."""


class DependencyError(WorkflowAgentError):
    """Raised when a transition violates dependency requirements."""


class InvalidTransitionError(WorkflowAgentError):
    """Raised when an action is not valid for the task's current state."""


class TaskCycleError(WorkflowAgentError):
    """Raised when the workflow definition contains dependency cycles."""


class TaskStatus(Enum):
    """Operational state for a workflow task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


def _normalize_sequence(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(str(item) for item in values if item is not None)


@dataclass(frozen=True)
class WorkflowTask:
    """Immutable definition for an individual workflow task."""

    id: str
    title: str
    description: str = ""
    phase: str | None = None
    owners: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    acceptance: tuple[str, ...] = ()
    deliverables: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "WorkflowTask":
        """Create a task from a dictionary-like payload."""

        owners: Iterable[str] | None
        owner_field = payload.get("owners")
        if owner_field is None:
            single_owner = payload.get("owner")
            if single_owner in (None, ""):
                owners = ()
            elif isinstance(single_owner, (list, tuple)):
                owners = single_owner
            else:
                owners = (single_owner,)
        elif isinstance(owner_field, str):
            owners = (owner_field,)
        else:
            owners = owner_field  # type: ignore[assignment]

        depends_on_field = payload.get("depends_on") or payload.get("dependencies")
        depends_on: Iterable[str] | None
        if depends_on_field is None:
            depends_on = ()
        elif isinstance(depends_on_field, str):
            depends_on = (depends_on_field,)
        else:
            depends_on = depends_on_field  # type: ignore[assignment]

        acceptance = payload.get("acceptance")
        deliverables = payload.get("deliverables") or payload.get("outputs")

        return cls(
            id=str(payload["id"]),
            title=str(payload.get("title", payload["id"])),
            description=str(payload.get("description", "")),
            phase=str(payload.get("phase")) if payload.get("phase") is not None else None,
            owners=_normalize_sequence(owners),
            depends_on=_normalize_sequence(depends_on),
            acceptance=_normalize_sequence(acceptance if isinstance(acceptance, Iterable) else None),
            deliverables=_normalize_sequence(
                deliverables if isinstance(deliverables, Iterable) else None
            ),
        )


@dataclass(frozen=True)
class WorkflowEvent:
    """Audit log entry emitted for every workflow mutation."""

    timestamp: datetime
    task_id: str
    actor: str
    action: str
    notes: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the event into basic Python types."""

        payload: Dict[str, Any] = {
            "timestamp": self.timestamp.isoformat(),
            "task_id": self.task_id,
            "actor": self.actor,
            "action": self.action,
        }
        if self.notes:
            payload["notes"] = self.notes
        if self.details:
            payload["details"] = dict(self.details)
        return payload


class QubeWorkflowAgent:
    """Main agent model for orchestrating Qube mission workflows."""

    def __init__(self, tasks: Sequence[WorkflowTask], *, name: str = "Qube Main Workflow") -> None:
        if not tasks:
            raise ValueError("at least one workflow task is required")

        self.name = name
        self._tasks: Dict[str, WorkflowTask] = {}
        for task in tasks:
            if task.id in self._tasks:
                raise ValueError(f"duplicate task id detected: {task.id}")
            self._tasks[task.id] = task

        self._validate_dependencies()

        self._status: Dict[str, TaskStatus] = {task_id: TaskStatus.PENDING for task_id in self._tasks}
        self._assignees: Dict[str, str | None] = {task_id: None for task_id in self._tasks}
        self._events: List[WorkflowEvent] = []
        self._started_at: Dict[str, datetime] = {}

        # Validate the graph once so we fail fast if a cycle exists.
        self._plan_cache: List[str] = self._topological_order()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_dict(cls, payload: Mapping[str, Any], *, name: str | None = None) -> "QubeWorkflowAgent":
        tasks_payload = payload.get("tasks")
        if not isinstance(tasks_payload, Sequence):
            raise ValueError("payload must include a sequence of tasks")
        tasks = [WorkflowTask.from_mapping(task) for task in tasks_payload]
        workflow_name = name or str(payload.get("name") or payload.get("title") or "Qube Main Workflow")
        return cls(tasks, name=workflow_name)

    @classmethod
    def from_yaml(cls, path: str | Sequence[str] | bytes | Mapping[str, Any], *, name: str | None = None) -> "QubeWorkflowAgent":
        """Instantiate the agent from a YAML roadmap file."""

        if yaml is None:
            raise RuntimeError("PyYAML is required to load YAML workflow definitions")

        if isinstance(path, Mapping):  # pragma: no cover - convenience path
            payload = path
        else:
            with open(path, "r", encoding="utf-8") as handle:
                payload = yaml.safe_load(handle)
        if not isinstance(payload, Mapping):
            raise ValueError("workflow YAML must define a mapping at the top level")
        return cls.from_dict(payload, name=name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def tasks(self) -> List[WorkflowTask]:
        """Return the task catalog in topological order."""

        return [self._tasks[task_id] for task_id in self._plan_cache]

    def task_status(self, task_id: str) -> TaskStatus:
        """Return the current status for a task."""

        self._assert_task(task_id)
        return self._status[task_id]

    def assignee(self, task_id: str) -> str | None:
        """Return the current assignee for a task, if any."""

        self._assert_task(task_id)
        return self._assignees[task_id]

    def ready_tasks(self) -> List[WorkflowTask]:
        """Return pending tasks whose dependencies are fully satisfied."""

        ready: List[WorkflowTask] = []
        for task in self._tasks.values():
            status = self._status[task.id]
            if status != TaskStatus.PENDING:
                continue
            if all(self._status[dep] == TaskStatus.COMPLETED for dep in task.depends_on):
                ready.append(task)
        ready.sort(key=lambda t: ((t.phase or ""), t.id))
        return ready

    def start_task(self, task_id: str, *, actor: str, notes: str = "", assignee: str | None = None) -> WorkflowEvent:
        """Transition a task into ``IN_PROGRESS`` once dependencies are satisfied."""

        task = self._assert_task(task_id)
        status = self._status[task_id]
        if status == TaskStatus.COMPLETED:
            raise InvalidTransitionError(f"task {task_id} is already completed")
        if status == TaskStatus.IN_PROGRESS:
            raise InvalidTransitionError(f"task {task_id} is already in progress")
        if status == TaskStatus.BLOCKED:
            raise InvalidTransitionError(f"task {task_id} is blocked and must be unblocked first")

        missing = [dep for dep in task.depends_on if self._status[dep] != TaskStatus.COMPLETED]
        if missing:
            raise DependencyError(f"task {task_id} cannot start; waiting on {', '.join(missing)}")

        event = self._record_event(
            task_id,
            actor=actor,
            action="start",
            notes=notes,
            details={"assignee": assignee} if assignee else {},
        )

        self._status[task_id] = TaskStatus.IN_PROGRESS
        self._started_at[task_id] = event.timestamp
        if assignee is not None:
            self._assignees[task_id] = assignee
        return event

    def complete_task(
        self,
        task_id: str,
        *,
        actor: str,
        notes: str = "",
        deliverables: Iterable[str] | None = None,
    ) -> WorkflowEvent:
        """Mark an in-progress task as completed and capture deliverables."""

        self._assert_task(task_id)
        status = self._status[task_id]
        if status == TaskStatus.PENDING:
            raise InvalidTransitionError(f"task {task_id} has not started")
        if status == TaskStatus.BLOCKED:
            raise InvalidTransitionError(f"task {task_id} is blocked; unblock before completing")
        if status != TaskStatus.IN_PROGRESS:
            raise InvalidTransitionError(f"task {task_id} cannot transition to completed from {status.value}")

        deliverable_items = _normalize_sequence(deliverables)
        event = self._record_event(
            task_id,
            actor=actor,
            action="complete",
            notes=notes,
            details={"deliverables": deliverable_items},
        )

        self._status[task_id] = TaskStatus.COMPLETED
        return event

    def block_task(self, task_id: str, *, actor: str, reason: str, notes: str = "") -> WorkflowEvent:
        """Block a task from progressing until follow-up work clears the issue."""

        self._assert_task(task_id)
        if not reason:
            raise ValueError("blocking a task requires a reason")

        event = self._record_event(
            task_id,
            actor=actor,
            action="block",
            notes=notes,
            details={"reason": reason},
        )

        self._status[task_id] = TaskStatus.BLOCKED
        return event

    def unblock_task(self, task_id: str, *, actor: str, notes: str = "") -> WorkflowEvent:
        """Return a blocked task to the ``PENDING`` queue."""

        self._assert_task(task_id)
        if self._status[task_id] != TaskStatus.BLOCKED:
            raise InvalidTransitionError(f"task {task_id} is not blocked")

        event = self._record_event(task_id, actor=actor, action="unblock", notes=notes)
        self._status[task_id] = TaskStatus.PENDING
        return event

    def reset_task(self, task_id: str, *, actor: str, reason: str, notes: str = "") -> WorkflowEvent:
        """Return a task to ``PENDING`` after auditing its work."""

        self._assert_task(task_id)
        if not reason:
            raise ValueError("resetting a task requires a reason")

        event = self._record_event(
            task_id,
            actor=actor,
            action="reset",
            notes=notes,
            details={"reason": reason},
        )

        self._status[task_id] = TaskStatus.PENDING
        self._assignees[task_id] = None
        self._started_at.pop(task_id, None)
        return event

    def status_summary(self) -> Dict[str, Any]:
        """Return a summary of workflow health suitable for dashboards."""

        counts: Dict[str, int] = {status.value: 0 for status in TaskStatus}
        for status in self._status.values():
            counts[status.value] += 1

        ready_ids = [task.id for task in self.ready_tasks()]
        return {
            "name": self.name,
            "counts": counts,
            "ready": ready_ids,
        }

    def history(self, task_id: str | None = None) -> List[WorkflowEvent]:
        """Return the full event log or the log for a specific task."""

        if task_id is None:
            return list(self._events)
        self._assert_task(task_id)
        return [event for event in self._events if event.task_id == task_id]

    def serialize_state(self) -> Dict[str, Any]:
        """Serialize the workflow for persistence or telemetry."""

        return {
            "name": self.name,
            "tasks": {
                task_id: {
                    "status": self._status[task_id].value,
                    "assignee": self._assignees[task_id],
                    "depends_on": list(self._tasks[task_id].depends_on),
                }
                for task_id in self._tasks
            },
            "ready": [task.id for task in self.ready_tasks()],
            "events": [event.to_dict() for event in self._events],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _assert_task(self, task_id: str) -> WorkflowTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:  # pragma: no cover - defensive path
            raise TaskNotFoundError(f"unknown task: {task_id}") from exc

    def _record_event(
        self,
        task_id: str,
        *,
        actor: str,
        action: str,
        notes: str = "",
        details: Mapping[str, Any] | None = None,
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            timestamp=datetime.now(timezone.utc),
            task_id=task_id,
            actor=actor,
            action=action,
            notes=notes,
            details=dict(details or {}),
        )
        self._events.append(event)
        return event

    def _validate_dependencies(self) -> None:
        missing: Dict[str, List[str]] = {}
        for task in self._tasks.values():
            unresolved = [dep for dep in task.depends_on if dep not in self._tasks]
            if unresolved:
                missing[task.id] = unresolved
        if missing:
            problems = ", ".join(f"{task} -> {', '.join(deps)}" for task, deps in sorted(missing.items()))
            raise DependencyError(f"workflow references unknown dependencies: {problems}")

    def _topological_order(self) -> List[str]:
        incoming: Dict[str, set[str]] = {
            task_id: set(task.depends_on) for task_id, task in self._tasks.items()
        }
        available = sorted([task_id for task_id, deps in incoming.items() if not deps])
        order: List[str] = []

        while available:
            task_id = available.pop(0)
            order.append(task_id)
            for candidate, deps in incoming.items():
                if task_id in deps:
                    deps.remove(task_id)
                    if not deps and candidate not in order and candidate not in available:
                        # Keep deterministic ordering by reinserting at the sorted position.
                        index = 0
                        while index < len(available) and available[index] < candidate:
                            index += 1
                        available.insert(index, candidate)

        if len(order) != len(self._tasks):
            raise TaskCycleError("workflow definition contains a dependency cycle")
        return order


__all__ = [
    "DependencyError",
    "InvalidTransitionError",
    "QubeWorkflowAgent",
    "TaskCycleError",
    "TaskNotFoundError",
    "TaskStatus",
    "WorkflowAgentError",
    "WorkflowEvent",
    "WorkflowTask",
]
