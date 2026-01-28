"""
Agency Hub - Portable Hub for Agentic Field Games.

This package provides the core infrastructure for normalizing environmental
states into a shared cognitive manifold.
"""

__version__ = "0.1.0"

from .tensor_field import TensorField
from .spoke_adapter import SpokeAdapter
from .docking_shell import DockingShell

__all__ = ["TensorField", "SpokeAdapter", "DockingShell"]
