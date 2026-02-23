from __future__ import annotations

from pathlib import Path


def emit_run_bundle(bundle_root: Path) -> Path:
    bundle_root.mkdir(parents=True, exist_ok=True)
    return bundle_root
