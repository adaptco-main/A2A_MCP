"""Determinism helpers used by validators and export logic."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
