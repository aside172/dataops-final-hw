import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_host: str
    app_port: int
    app_env: str
    request_log_level: str
    model_version: str
    database_url: str
    default_threshold: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "ml-risk-service"),
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        app_env=os.getenv("APP_ENV", "dev"),
        request_log_level=os.getenv("REQUEST_LOG_LEVEL", "INFO"),
        model_version=os.getenv("MODEL_VERSION", "2026.03.15"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/ml_service.sqlite3"),
        default_threshold=float(os.getenv("DEFAULT_THRESHOLD", "0.65")),
    )
