"""Root conftest.py — ensures project root is on sys.path and configures pytest-asyncio."""
import sys
from pathlib import Path

# Insert project root so `from orchestrator...` and `from agents...` work everywhere
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
