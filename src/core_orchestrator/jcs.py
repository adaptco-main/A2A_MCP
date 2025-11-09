"""Triadic backbone definitions for ZERO-DRIFT attestation flows.

This module models the canonical flow topology described in the World OS briefing.
The data structures are deliberately lightweight so downstream services—dashboards,
ledger writers, or simulation harnesses—can import them without triggering heavy
orchestration logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class FlowEdge:
    """Represents a directional relationship between layers in the backbone."""

    source: str
    target: str
    channel: str
    guard: str

    def zero_drift_guarded(self) -> bool:
        """Return True when the guard enforces ZERO-DRIFT semantics."""
        return "ZERO_DRIFT" in self.guard.upper()


@dataclass
class TriadicBackbone:
    """Encapsulates the tri-layer attestation topology."""

    layers: Mapping[str, str]
    flows: Iterable[FlowEdge]
    integrity_protocol: str = "ZERO_DRIFT"
    _adjacency_cache: Dict[str, List[str]] = field(default_factory=dict, init=False, repr=False)

    def as_adjacency(self) -> Dict[str, List[str]]:
        """Return an adjacency list keyed by layer name."""
        if not self._adjacency_cache:
            adjacency: Dict[str, List[str]] = {layer: [] for layer in self.layers}
            for edge in self.flows:
                adjacency.setdefault(edge.source, []).append(edge.target)
            self._adjacency_cache = {node: sorted(targets) for node, targets in adjacency.items()}
        return dict(self._adjacency_cache)

    def zero_drift_attested(self) -> bool:
        """Verify that the topology enforces ZERO-DRIFT across all flows."""
        if self.integrity_protocol.upper() != "ZERO_DRIFT":
            return False
        return all(edge.zero_drift_guarded() for edge in self.flows)


DEFAULT_TRIADIC_BACKBONE = TriadicBackbone(
    layers={
        "codex_operational": "Codex commits and runtime patches",
        "chatgpt_creative": "Workspace capsules and scene definitions",
        "p3l_philosophical": "Purpose-driven execution contracts",
        "qube_core": "Central attestation nexus",
    },
    flows=(
        FlowEdge(
            source="codex_operational",
            target="qube_core",
            channel="commit_attestation",
            guard="ZERO_DRIFT_SIGNATURE",
        ),
        FlowEdge(
            source="chatgpt_creative",
            target="qube_core",
            channel="capsule_projection",
            guard="ZERO_DRIFT_SYNTHESIS",
        ),
        FlowEdge(
            source="p3l_philosophical",
            target="qube_core",
            channel="ethics_constraint",
            guard="ZERO_DRIFT_CANON",
        ),
        FlowEdge(
            source="qube_core",
            target="codex_operational",
            channel="attestation_receipt",
            guard="ZERO_DRIFT_FEEDBACK",
        ),
        FlowEdge(
            source="qube_core",
            target="chatgpt_creative",
            channel="capsule_alignment",
            guard="ZERO_DRIFT_FEEDBACK",
        ),
        FlowEdge(
            source="qube_core",
            target="p3l_philosophical",
            channel="integrity_protocol",
            guard="ZERO_DRIFT_FEEDBACK",
        ),
    ),
)


__all__ = [
    "FlowEdge",
    "TriadicBackbone",
    "DEFAULT_TRIADIC_BACKBONE",
]
