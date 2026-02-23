#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

TARGET_PATHS = {
    "src/prime_directive/api/app.py": "API entrypoint",
    "src/prime_directive/pipeline/engine.py": "Pipeline orchestrator",
    "src/prime_directive/validators/preflight.py": "Preflight validator",
    "src/prime_directive/sovereignty/chain.py": "Sovereignty chain",
    "scripts/smoke_ws.sh": "WS smoke script",
    "docs/architecture/ws_protocol.md": "WS protocol doc",
}

FORBIDDEN_PATTERNS = [
    "exports/**",
    "staging/**",
    "*.db",
    ".env",
]

MOVE_HINTS = {
    "app/multi_client_api.py": "src/prime_directive/api/app.py (adapter wrap)",
    "src/multi_client_router.py": "src/prime_directive/pipeline/engine.py (adapter wrap)",
    "orchestrator/stateflow.py": "src/prime_directive/pipeline/state_machine.py",
}


def _glob_any(pattern: str) -> list[Path]:
    return [p for p in Path(".").glob(pattern) if p.is_file()]


def main() -> int:
    print("# PRIME_DIRECTIVE repository audit")
    print("\n[Target coverage]")
    for rel, desc in TARGET_PATHS.items():
        status = "OK" if Path(rel).exists() else "MISSING"
        print(f"- {status:7} {rel} :: {desc}")

    print("\n[Layering warnings]")
    ws_candidates = [p for p in Path(".").glob("**/*.py") if "ws" in p.name.lower() or "api" in p.name.lower()]
    for path in sorted(ws_candidates):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "validate_" in text and "websocket" in text.lower():
            print(f"- WARN {path}: potential gate logic in transport layer")

    print("\n[Forbidden committed artifacts]")
    any_forbidden = False
    for pattern in FORBIDDEN_PATTERNS:
        matches = _glob_any(pattern)
        for match in matches:
            any_forbidden = True
            print(f"- BLOCKER {match}")
    if not any_forbidden:
        print("- none")

    print("\n[Suggested move targets]")
    for src, dst in MOVE_HINTS.items():
        if Path(src).exists():
            print(f"- {src} -> {dst}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
