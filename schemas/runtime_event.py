"""Internal runtime event DTOs for orchestration and adapter boundaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    """Canonical tool invocation request parsed from agent/provider output."""

    tool_name: str = Field(..., min_length=1)
    arguments: Dict[str, Any] = Field(default_factory=dict)


class EventPayload(BaseModel):
    """Canonical envelope payload consumed by the orchestrator."""

    content: Any
    tool_request: ToolRequest | None = None
    status: str | None = None
    provider: str | None = None
    raw: Dict[str, Any] = Field(default_factory=dict)


class RuntimeEvent(BaseModel):
    """Canonical runtime event preserving causal lineage across hops."""

    trace_id: str = Field(..., min_length=1)
    span_id: str = Field(default_factory=lambda: uuid4().hex)
    parent_span_id: str | None = None
    event_type: str = Field(..., min_length=1)
    content: EventPayload
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def next_hop(
        self,
        *,
        event_type: str,
        content: EventPayload,
    ) -> "RuntimeEvent":
        """Emit a child event hop with the same trace and a fresh span."""
        return RuntimeEvent(
            trace_id=self.trace_id,
            span_id=uuid4().hex,
            parent_span_id=self.span_id,
            event_type=event_type,
            content=content,
        )
