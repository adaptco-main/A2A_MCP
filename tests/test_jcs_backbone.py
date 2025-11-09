import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from core_orchestrator.jcs import DEFAULT_TRIADIC_BACKBONE


def test_default_backbone_zero_drift_guards():
    assert DEFAULT_TRIADIC_BACKBONE.zero_drift_attested()


def test_default_backbone_adjacency_contains_all_layers():
    adjacency = DEFAULT_TRIADIC_BACKBONE.as_adjacency()
    # Each defined layer should appear even if it has no outbound edges.
    for layer in DEFAULT_TRIADIC_BACKBONE.layers:
        assert layer in adjacency

    # The Qube core should route feedback to every other layer.
    assert set(adjacency["qube_core"]) == {
        "codex_operational",
        "chatgpt_creative",
        "p3l_philosophical",
    }
