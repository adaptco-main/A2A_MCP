#!/usr/bin/env python3
"""CLI entrypoint for interacting with the CODEX qernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from codex_qernel import CodexQernel, QernelConfig


def _default_base_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the AxQxOS CODEX qernel runtime")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=_default_base_dir(),
        help="Repository root containing capsules/ and log directories.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("health", help="Display qernel health information")

    capsules = sub.add_parser("capsules", help="List discovered capsules")
    capsules.add_argument("--refresh", action="store_true", help="Refresh capsule catalog before listing")

    show = sub.add_parser("show", help="Show a capsule manifest")
    show.add_argument("capsule_id", help="Identifier of the capsule to display")

    sub.add_parser("refresh", help="Force a capsule refresh")

    events = sub.add_parser("events", help="Print recent qernel events")
    events.add_argument("--limit", type=int, default=20, help="Number of events to show")

    emit = sub.add_parser("emit", help="Record an ad-hoc qernel event")
    emit.add_argument("event", help="Event name to emit")
    emit.add_argument(
        "--payload",
        default="{}",
        help="JSON payload describing the event context",
    )

    rehearsal = sub.add_parser(
        "rehearsal", help="Emit the rehearsal scrollstream ledger cycle"
    )
    rehearsal.add_argument(
        "--live",
        action="store_false",
        dest="training_mode",
        help="Emit the rehearsal in live mode (non-deterministic overlay)",
    )
    rehearsal.set_defaults(training_mode=True)
    return parser


def _load_payload(data: str) -> Dict[str, Any]:
    try:
        result = json.loads(data)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON payload: {exc}")
    if not isinstance(result, dict):
        raise SystemExit("payload must be a JSON object")
    return result


def main(args: list[str] | None = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(args)

    config = QernelConfig.from_env(base_dir=parsed.base_dir)
    qernel = CodexQernel(config)

    if parsed.command == "health":
        print(json.dumps(qernel.health_status(), indent=2))
        return 0

    if parsed.command == "capsules":
        if parsed.refresh:
            qernel.refresh()
        print(json.dumps({"capsules": qernel.list_capsules()}, indent=2))
        return 0

    if parsed.command == "show":
        manifest = qernel.get_capsule(parsed.capsule_id)
        if manifest is None:
            raise SystemExit(f"capsule not found: {parsed.capsule_id}")
        print(json.dumps(manifest, indent=2))
        return 0

    if parsed.command == "refresh":
        qernel.refresh()
        print(json.dumps({"status": "refreshed", "capsule_count": len(qernel.list_capsules())}, indent=2))
        return 0

    if parsed.command == "events":
        events = [event.__dict__ for event in qernel.read_events(limit=parsed.limit)]
        print(json.dumps({"events": events}, indent=2))
        return 0

    if parsed.command == "emit":
        payload = _load_payload(parsed.payload)
        event = qernel.record_event(parsed.event, payload)
        print(json.dumps(event.__dict__, indent=2))
        return 0

    if parsed.command == "rehearsal":
        entries = qernel.emit_scrollstream_rehearsal(training_mode=parsed.training_mode)
        print(json.dumps({"entries": entries}, indent=2))
        return 0

    parser.error(f"unsupported command: {parsed.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
