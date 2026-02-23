from __future__ import annotations

from pathlib import Path

from prime_directive.util.paths import enforce_allowed_root


def export_artifact(path: str, content: bytes) -> Path:
    target = enforce_allowed_root(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target
