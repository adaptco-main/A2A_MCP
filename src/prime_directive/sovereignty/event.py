from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SovereigntyEvent:
    event_type: str
    state: str
    payload: dict[str, Any]
    prev_hash: str | None = None
