from __future__ import annotations

from pathlib import Path


ALLOWED_ROOTS = (Path("staging").resolve(), Path("exports").resolve())


def enforce_allowed_root(path: str | Path) -> Path:
    candidate = Path(path).resolve()
    if not any(root == candidate or root in candidate.parents for root in ALLOWED_ROOTS):
        raise ValueError(f"Path is outside allowed roots: {candidate}")
    return candidate
