"""Telemetry and runbook helpers for protected MCP ingestion."""

from __future__ import annotations

import json
import logging
import math
from bisect import insort
from collections import defaultdict
from dataclasses import dataclass
from time import time
from typing import Any

LOGGER = logging.getLogger("a2a.telemetry")

RUNBOOK_INGESTION_TRIAGE = "https://runbooks.a2a.local/oncall/protected-ingestion"
RUNBOOK_TOKEN_SHAPING = "https://runbooks.a2a.local/oncall/token-shaping"


@dataclass(frozen=True)
class TelemetryTimer:
    """Small context object used to track protected ingestion latencies."""

    started_at: float


class TelemetryRecorder:
    """In-memory metrics recorder with structured logs for on-call triage."""

    def __init__(self) -> None:
        self._counters: defaultdict[str, int] = defaultdict(int)
        self._latency_ms: list[float] = []

    def start_timer(self) -> TelemetryTimer:
        return TelemetryTimer(started_at=time())

    def record_request_outcome(
        self,
        *,
        avatar_id: str,
        client_id: str,
        outcome: str,
        rejection_reason: str | None = None,
        runbook_url: str = RUNBOOK_INGESTION_TRIAGE,
    ) -> None:
        key = f"mcp.ingestion.requests|avatar:{avatar_id}|client:{client_id}|outcome:{outcome}"
        self._counters[key] += 1
        if rejection_reason:
            self._counters[f"mcp.ingestion.rejections|reason:{rejection_reason}"] += 1

        self._log(
            "ingestion.request.outcome",
            avatar_id=avatar_id,
            client_id=client_id,
            outcome=outcome,
            rejection_reason=rejection_reason,
            runbook_url=runbook_url,
        )

    def observe_protected_ingestion_latency(self, timer: TelemetryTimer, *, client_id: str) -> None:
        latency_ms = max((time() - timer.started_at) * 1000.0, 0.0)
        insort(self._latency_ms, latency_ms)
        self._log(
            "ingestion.latency",
            client_id=client_id,
            latency_ms=round(latency_ms, 3),
            p50_ms=round(self.latency_percentile(50), 3),
            p95_ms=round(self.latency_percentile(95), 3),
            p99_ms=round(self.latency_percentile(99), 3),
            runbook_url=RUNBOOK_INGESTION_TRIAGE,
        )

    def record_token_shaping_stage(
        self,
        *,
        stage: str,
        tenant_id: str,
        token_count: int,
        embedding_hash: str,
    ) -> None:
        self._counters[f"mcp.token_shaping.stage|tenant:{tenant_id}|stage:{stage}"] += 1
        self._log(
            "token_shaping.stage",
            stage=stage,
            tenant_id=tenant_id,
            token_count=token_count,
            embedding_hash=embedding_hash,
            runbook_url=RUNBOOK_TOKEN_SHAPING,
        )

    def record_hash_anomaly(
        self,
        *,
        tenant_id: str,
        stage: str,
        embedding_hash: str,
        anomaly: str,
    ) -> None:
        self._counters[f"mcp.token_shaping.hash_anomaly|tenant:{tenant_id}|stage:{stage}|anomaly:{anomaly}"] += 1
        self._log(
            "token_shaping.hash.anomaly",
            tenant_id=tenant_id,
            stage=stage,
            embedding_hash=embedding_hash,
            anomaly=anomaly,
            runbook_url=RUNBOOK_TOKEN_SHAPING,
        )

    def latency_percentile(self, percentile: int) -> float:
        if not self._latency_ms:
            return 0.0
        idx = max(min(math.ceil((percentile / 100.0) * len(self._latency_ms)) - 1, len(self._latency_ms) - 1), 0)
        return float(self._latency_ms[idx])

    def _log(self, event: str, **fields: Any) -> None:
        LOGGER.info(json.dumps({"event": event, **fields}, sort_keys=True))


TELEMETRY = TelemetryRecorder()
