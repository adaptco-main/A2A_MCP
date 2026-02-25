"""
Prometheus metrics for VH2 Validator + A2A Orchestrator.

Exposes:
- a2a_orchestrator_requests_total{result="success|halt|error"}
- a2a_orchestrator_plan_ingress_total{status="created|resumed|error"}
- a2a_orchestrator_verification_results_total{valid="true|false"}
- a2a_orchestrator_duration_ms (histogram)
"""

from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

# Use the global default registry
registry = REGISTRY

# ──── Orchestration Request Counter ────
request_counter = Counter(
    'a2a_orchestrator_requests_total',
    'Total orchestrator requests by result type',
    labelnames=['result'],  # values: 'success', 'halt', 'error'
    registry=registry
)

# ──── Plan Ingress Counter ────
plan_counter = Counter(
    'a2a_orchestrator_plan_ingress_total',
    'Total plan ingress events by status',
    labelnames=['status'],  # values: 'created', 'resumed', 'error'
    registry=registry
)

# ──── Verification Results Counter ────
verification_counter = Counter(
    'a2a_orchestrator_verification_results_total',
    'Total verification operations by validity',
    labelnames=['valid'],  # values: 'true', 'false'
    registry=registry
)

# ──── System Halt Breakdown ────
halt_counter = Counter(
    'a2a_orchestrator_system_halt_total',
    'Total SYSTEM_HALT decisions by reason',
    labelnames=['reason'],  # values: 'missing_fields', 'out_of_range', 'invalid_schema', 'timeout'
    registry=registry
)

# ──── Request Duration Histogram (milliseconds) ────
duration_histogram = Histogram(
    'a2a_orchestrator_duration_ms',
    'Orchestrator operation latency in milliseconds',
    labelnames=['result'],  # values: 'success', 'halt', 'error'
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2000, 5000],  # ms
    registry=registry
)

def record_request(result: str, duration_ms: float = 0, halt_reason: str = None):
    """
    Update request counters and latency histograms.
    """
    request_counter.labels(result=result).inc()
    duration_histogram.labels(result=result).observe(duration_ms)
    if result == 'halt' and halt_reason:
        halt_counter.labels(reason=halt_reason).inc()

def record_plan_ingress(status: str):
    """
    Update plan ingress counters.
    """
    plan_counter.labels(status=status).inc()

def record_verification(valid: bool):
    """
    Record a verification result.
    """
    verification_counter.labels(valid='true' if valid else 'false').inc()
