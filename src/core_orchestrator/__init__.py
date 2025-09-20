"""Core orchestrator package for routing parsed events to downstream sinks."""

from .cli import main
from .parsers import DiscordMessage, DiscordParser
from .router import Event, Router
from .sinks import GoogleCalendarSink, NotionSink, ShopifySink

__all__ = [
    "DiscordMessage",
    "DiscordParser",
    "Event",
    "GoogleCalendarSink",
    "NotionSink",
    "Router",
    "ShopifySink",
    "main",
]
__version__ = "0.1.0"
