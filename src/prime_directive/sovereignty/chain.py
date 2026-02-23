from __future__ import annotations

from dataclasses import asdict

from prime_directive.sovereignty.event import SovereigntyEvent
from prime_directive.util.determinism import canonical_json
from prime_directive.util.hashing import sha256_hex


def event_fingerprint(event: SovereigntyEvent) -> str:
    """Deterministic fingerprint with canonical JSON, no wall-clock timestamps."""
    return sha256_hex(canonical_json(asdict(event)))


def verify_link(current: SovereigntyEvent, previous_hash: str | None) -> bool:
    return current.prev_hash == previous_hash
