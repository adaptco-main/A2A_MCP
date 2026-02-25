from prometheus_client import Counter, Histogram

# Request metrics
REQUEST_COUNT = Counter(
    "orchestrator_requests_total",
    "Total orchestrator requests",
    ["result", "halt_reason"]
)
REQUEST_DURATION = Histogram(
    "orchestrator_request_duration_ms",
    "Request duration in milliseconds",
    ["result"]
)

# Ingress metrics
PLAN_INGRESS_COUNT = Counter(
    "orchestrator_plan_ingress_total",
    "Total plan ingress events",
    ["status"]
)

def record_request(result: str, duration_ms: float, halt_reason: str = "none"):
    REQUEST_COUNT.labels(result=result, halt_reason=halt_reason).inc()
    REQUEST_DURATION.labels(result=result).observe(duration_ms)

def record_plan_ingress(status: str):
    PLAN_INGRESS_COUNT.labels(status=status).inc()
