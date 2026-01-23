"""Runtime support package for the CODEX qernel powering AxQxOS."""

from __future__ import annotations

from .config import QernelConfig
from .geodesic import GeodesicTerminalModel, GeodesicSegment, build_geodesic_terminal
from .psm import GaussianActionResult, PSMState, gaussian_action_synth, load_psm_state
from .runtime import CodexQernel, QernelEvent

__all__ = [
    "CodexQernel",
    "QernelConfig",
    "QernelEvent",
    "GeodesicSegment",
    "GeodesicTerminalModel",
    "build_geodesic_terminal",
    "GaussianActionResult",
    "PSMState",
    "gaussian_action_synth",
    "load_psm_state",
]

__version__ = "1.0.0"
