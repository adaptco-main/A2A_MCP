"""Core MCP package for shared protocol logic with tenant isolation."""

from a2a_mcp.client_token_pipe import (
    ClientTokenPipe,
    ClientTokenPipeContext,
    ContaminationError,
    InMemoryEventStore,
)
from a2a_mcp.mcp_core import MCPCore, MCPResult

__all__ = [
    "MCPCore",
    "MCPResult",
    "ClientTokenPipe",
    "ClientTokenPipeContext",
    "ContaminationError",
    "InMemoryEventStore",
]
