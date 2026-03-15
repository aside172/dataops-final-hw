import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test_service.sqlite3"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app

def test_healthz() -> None:
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_predict_success() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/predict",
            json={"income": 4500, "debt": 1800, "utilization": 0.42},
            headers={"X-Request-Id": "test-request"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert set(payload) == {"risk_score", "will_default", "model_version", "duration_ms"}
        assert 0 <= payload["risk_score"] <= 1


def test_predict_validation() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/predict", json={"income": -1, "debt": 100, "utilization": 0.4})
        assert response.status_code == 422


def test_metrics_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "ml_service_http_requests_total" in response.text
