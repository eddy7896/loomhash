"""Admin storage backend for the Developer Dashboard.

Provides real-time storage and retrieval for analytics, usage metering (billing),
and project settings.
"""

from __future__ import annotations

import abc
import json
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class APIEvent:
    key_id: str | None
    endpoint: str
    status_code: int
    latency_ms: int
    created_at: int | None = None


class AdminStore(abc.ABC):
    @abc.abstractmethod
    def log_event(self, event: APIEvent) -> None:
        """Log an API request event for analytics and billing."""

    @abc.abstractmethod
    def get_analytics(self) -> dict[str, Any]:
        """Return aggregated analytics data (e.g. request counts, success rates)."""

    @abc.abstractmethod
    def get_billing(self) -> dict[str, Any]:
        """Return current billing cycle usage and costs."""

    @abc.abstractmethod
    def get_settings(self) -> dict[str, str]:
        """Return all project settings."""

    @abc.abstractmethod
    def set_setting(self, key: str, value: str) -> None:
        """Update a project setting."""


class InMemoryAdminStore(AdminStore):
    """In-memory admin store for dev and testing."""

    def __init__(self) -> None:
        self._events: list[APIEvent] = []
        self._settings: dict[str, str] = {"project_name": "LoomHash Auth"}

    def log_event(self, event: APIEvent) -> None:
        event.created_at = int(time.time())
        self._events.append(event)

    def get_analytics(self) -> dict[str, Any]:
        total = len(self._events)
        successes = sum(1 for e in self._events if e.status_code == 200)
        failures = total - successes
        success_rate = (successes / total * 100) if total > 0 else 100.0

        return {
            "total_requests": total,
            "success_rate_percent": round(success_rate, 2),
            "total_failures": failures,
            "recent_events": [
                {
                    "endpoint": e.endpoint,
                    "status_code": e.status_code,
                    "latency_ms": e.latency_ms,
                    "created_at": e.created_at,
                }
                for e in self._events[-50:]
            ],
        }

    def get_billing(self) -> dict[str, Any]:
        # Metering calculation: $0.05 per API call
        total_requests = len(self._events)
        cost = total_requests * 0.05
        return {
            "current_cycle_requests": total_requests,
            "current_cycle_cost_usd": round(cost, 2),
            "plan_limit_requests": 10000,
            "currency": "USD",
        }

    def get_settings(self) -> dict[str, str]:
        return dict(self._settings)

    def set_setting(self, key: str, value: str) -> None:
        self._settings[key] = value


class PostgresAdminStore(AdminStore):
    """Postgres-backed admin store."""

    def __init__(self, conninfo: str) -> None:
        import psycopg
        self._conninfo = conninfo
        self._conn = psycopg.connect(conninfo, autocommit=True)

    def ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_events (
                id SERIAL PRIMARY KEY,
                key_id TEXT,
                endpoint TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS project_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )

    def log_event(self, event: APIEvent) -> None:
        self._conn.execute(
            """
            INSERT INTO api_events (key_id, endpoint, status_code, latency_ms)
            VALUES (%s, %s, %s, %s)
            """,
            (event.key_id, event.endpoint, event.status_code, event.latency_ms),
        )

    def get_analytics(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) FROM api_events").fetchone()[0]
        successes = self._conn.execute("SELECT COUNT(*) FROM api_events WHERE status_code = 200").fetchone()[0]
        failures = total - successes
        success_rate = (successes / total * 100) if total > 0 else 100.0

        rows = self._conn.execute(
            "SELECT endpoint, status_code, latency_ms, EXTRACT(EPOCH FROM created_at) "
            "FROM api_events ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

        recent_events = [
            {
                "endpoint": r[0],
                "status_code": r[1],
                "latency_ms": r[2],
                "created_at": int(r[3]),
            }
            for r in rows
        ]

        return {
            "total_requests": total,
            "success_rate_percent": round(success_rate, 2),
            "total_failures": failures,
            "recent_events": recent_events,
        }

    def get_billing(self) -> dict[str, Any]:
        total = self._conn.execute("SELECT COUNT(*) FROM api_events").fetchone()[0]
        cost = total * 0.05
        return {
            "current_cycle_requests": total,
            "current_cycle_cost_usd": round(cost, 2),
            "plan_limit_requests": 10000,
            "currency": "USD",
        }

    def get_settings(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT key, value FROM project_settings").fetchall()
        settings = {r[0]: r[1] for r in rows}
        if "project_name" not in settings:
            settings["project_name"] = "LoomHash Auth"
        return settings

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            """
            INSERT INTO project_settings (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, value),
        )
