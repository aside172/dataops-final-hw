import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import psycopg


CREATE_TABLE_SQL_POSTGRES = """
CREATE TABLE IF NOT EXISTS prediction_logs (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    input_payload JSONB NOT NULL,
    output_payload JSONB NOT NULL,
    duration_ms DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

CREATE_TABLE_SQL_SQLITE = """
CREATE TABLE IF NOT EXISTS prediction_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    input_payload TEXT NOT NULL,
    output_payload TEXT NOT NULL,
    duration_ms REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


class PredictionLogRepository:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn

    def _is_sqlite(self) -> bool:
        return self.dsn.startswith("sqlite:///")

    def _sqlite_path(self) -> str:
        return self.dsn.replace("sqlite:///", "", 1)

    def _ensure_sqlite_parent(self) -> None:
        Path(self._sqlite_path()).parent.mkdir(parents=True, exist_ok=True)

    def init_schema(self) -> None:
        if self._is_sqlite():
            self._ensure_sqlite_parent()
            with closing(sqlite3.connect(self._sqlite_path())) as conn:
                conn.execute(CREATE_TABLE_SQL_SQLITE)
                conn.commit()
            return

        with closing(psycopg.connect(self.dsn)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(CREATE_TABLE_SQL_POSTGRES)
            conn.commit()

    def save(self, request_id: str, model_version: str, payload_in: dict[str, Any], payload_out: dict[str, Any], duration_ms: float) -> None:
        if self._is_sqlite():
            self._ensure_sqlite_parent()
            with closing(sqlite3.connect(self._sqlite_path())) as conn:
                conn.execute(
                    """
                    INSERT INTO prediction_logs (request_id, model_version, input_payload, output_payload, duration_ms)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        model_version,
                        json.dumps(payload_in),
                        json.dumps(payload_out),
                        duration_ms,
                    ),
                )
                conn.commit()
            return

        with closing(psycopg.connect(self.dsn)) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO prediction_logs (request_id, model_version, input_payload, output_payload, duration_ms)
                    VALUES (%s, %s, %s::jsonb, %s::jsonb, %s)
                    """,
                    (
                        request_id,
                        model_version,
                        json.dumps(payload_in),
                        json.dumps(payload_out),
                        duration_ms,
                    ),
                )
            conn.commit()

    def database_name(self) -> str:
        if self._is_sqlite():
            return self._sqlite_path()
        return urlparse(self.dsn).path.lstrip("/")
