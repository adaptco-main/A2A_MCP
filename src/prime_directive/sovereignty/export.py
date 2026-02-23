from __future__ import annotations

from dataclasses import asdict

from prime_directive.sovereignty.event import SovereigntyEvent
from prime_directive.util.determinism import canonical_json


def export_chain(events: list[SovereigntyEvent]) -> str:
    return canonical_json([asdict(event) for event in events])
