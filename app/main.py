import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging_utils import configure_logging, log_json
from app.metrics import MODEL_INFERENCE, MODEL_PREDICTIONS, REQUEST_COUNT, REQUEST_LATENCY, metrics_response
from app.model import CreditRiskModel
from app.schemas import PredictRequest, PredictResponse
from app.storage import PredictionLogRepository

settings = get_settings()
configure_logging(settings.request_log_level)

logger = logging.getLogger("ml-service")
repository = PredictionLogRepository(settings.database_url)
model = CreditRiskModel(version=settings.model_version, threshold=settings.default_threshold)


@asynccontextmanager
async def lifespan(_: FastAPI):
    repository.init_schema()
    log_json(
        logger,
        logging.INFO,
        "Application startup complete",
        event="startup",
        database=repository.database_name(),
        model_version=settings.model_version,
    )
    yield


app = FastAPI(title="ML Risk Service", version=settings.model_version, lifespan=lifespan)


@app.middleware("http")
async def request_metrics_and_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - started) * 1000, 3)
        REQUEST_COUNT.labels(request.method, request.url.path, "500").inc()
        REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration_ms / 1000)
        log_json(
            logger,
            logging.ERROR,
            "Unhandled request error",
            event="request",
            request_id=request_id,
            path=request.url.path,
            method=request.method,
            status_code=500,
            duration_ms=duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - started) * 1000, 3)
    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(duration_ms / 1000)
    response.headers["X-Request-Id"] = request_id
    log_json(
        logger,
        logging.INFO,
        "Request served",
        event="request",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz() -> dict[str, str]:
    return {"status": "ready", "model_version": settings.model_version}


@app.get("/metrics")
async def metrics():
    return metrics_response()


@app.post("/api/v1/predict", response_model=PredictResponse)
async def predict(payload: PredictRequest, request: Request) -> PredictResponse:
    started = time.perf_counter()
    prediction = model.predict(payload.income, payload.debt, payload.utilization)
    duration_ms = round((time.perf_counter() - started) * 1000, 3)

    MODEL_INFERENCE.labels(settings.model_version).observe(duration_ms / 1000)
    MODEL_PREDICTIONS.labels(settings.model_version, str(prediction.will_default).lower()).inc()

    response_payload = {
        "risk_score": prediction.risk_score,
        "will_default": prediction.will_default,
        "model_version": prediction.version,
        "duration_ms": duration_ms,
    }
    repository.save(
        request_id=request.headers.get("X-Request-Id", str(uuid.uuid4())),
        model_version=prediction.version,
        payload_in=payload.model_dump(),
        payload_out=response_payload,
        duration_ms=duration_ms,
    )
    return PredictResponse(**response_payload)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "service": settings.app_name,
            "version": settings.model_version,
            "docs": "/docs",
            "predict_endpoint": "/api/v1/predict",
            "metrics_endpoint": "/metrics",
        }
    )
