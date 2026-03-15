from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response


REQUEST_COUNT = Counter(
    "ml_service_http_requests_total",
    "Total HTTP requests served by the ML service",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "ml_service_http_request_duration_seconds",
    "Latency of HTTP requests",
    ["method", "path"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2, 5),
)

MODEL_INFERENCE = Histogram(
    "ml_service_model_inference_duration_seconds",
    "Latency of model predictions",
    ["model_version"],
    buckets=(0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2),
)

MODEL_PREDICTIONS = Counter(
    "ml_service_predictions_total",
    "Total model predictions",
    ["model_version", "prediction"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
