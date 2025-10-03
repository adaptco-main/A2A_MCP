"""CODEX qernel runtime implementation for AxQxOS."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import threading

from .config import QernelConfig
from .capsules import CapsuleManifest, discover_capsule_manifests, map_capsules_by_id


@dataclass(frozen=True)
class QernelEvent:
    """Represents a single event emitted by the qernel."""

    ts: str
    event: str
    payload: Dict[str, Any]

    def to_json(self) -> str:
        body = {
            "ts": self.ts,
            "event": self.event,
            "payload": self.payload,
        }
        return json.dumps(body, ensure_ascii=False, separators=(",", ":"))


class CodexQernel:
    """Manage capsule manifests and operational events for AxQxOS."""

    def __init__(self, config: QernelConfig):
        self.config = config
        self._lock = threading.Lock()
        self._capsules: Dict[str, CapsuleManifest] = {}
        self._last_refresh: Optional[datetime] = None
        self.config.ensure_directories()
        if self.config.auto_refresh:
            self.refresh(emit_event=False)

    # Capsule management -------------------------------------------------
    def refresh(self, *, emit_event: bool = True) -> None:
        """Reload capsule manifests from disk."""

        manifests = discover_capsule_manifests(Path(self.config.capsules_dir))
        mapping = map_capsules_by_id(manifests)
        refreshed_at = datetime.now(timezone.utc)
        with self._lock:
            self._capsules = mapping
            self._last_refresh = refreshed_at
        if emit_event:
            self.record_event(
                "codex.qernel.refreshed",
                {
                    "capsule_count": len(mapping),
                    "capsules": sorted(mapping.keys()),
                },
            )

    def list_capsules(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [manifest.short_dict() for manifest in self._capsules.values()]

    def get_capsule(self, capsule_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            manifest = self._capsules.get(capsule_id)
            return manifest.raw if manifest else None

    # Event handling -----------------------------------------------------
    def record_event(self, event: str, payload: Dict[str, Any]) -> QernelEvent:
        timestamp = datetime.now(timezone.utc).isoformat()
        qernel_event = QernelEvent(ts=timestamp, event=event, payload=payload)
        log_path = Path(self.config.events_log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(qernel_event.to_json() + "\n")
        return qernel_event

    def read_events(self, *, limit: int = 20) -> List[QernelEvent]:
        log_path = Path(self.config.events_log)
        if not log_path.exists():
            return []
        with log_path.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        events: List[QernelEvent] = []
        for raw in lines[-limit:]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                data = json.loads(raw)
                events.append(
                    QernelEvent(
                        ts=str(data.get("ts", "")),
                        event=str(data.get("event", "")),
                        payload=dict(data.get("payload", {})),
                    )
                )
            except json.JSONDecodeError:
                continue
        return events

    # Health -------------------------------------------------------------
    def health_status(self) -> Dict[str, Any]:
        with self._lock:
            refresh_at = self._last_refresh.isoformat() if self._last_refresh else None
            capsule_ids = sorted(self._capsules.keys())
        status = {
            "status": "ok",
            "os": self.config.os_name,
            "qernel_version": self.config.qernel_version,
            "capsules_loaded": len(capsule_ids),
            "capsules": capsule_ids,
            "last_refresh": refresh_at,
        }
        return status
