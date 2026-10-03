"""PostgreSQL persistence layer for Maritime AI System (phase 3, made real 2026-10-02).

Phase 2 made the API real on an in-process store. Phase 3 makes the store
survive restarts: write-through to PostgreSQL via asyncpg, hydration on
startup. The API never depends on the database being reachable — if Postgres
is down, the API runs degraded on the in-memory store and /status says so.

Design:
- asyncpg pool, plain postgresql:// URL (the +asyncpg SQLAlchemy form is stripped).
- Schema is bootstrapped idempotently (CREATE TABLE IF NOT EXISTS) from here,
  not init_db.sql, so tests and fresh deploys need no manual DDL.
- Hydration loads ships, crew, decisions, telemetry and notifications back
  into the Store and fixes the id sequences.
- Every persist_* is best-effort: failures are logged and surfaced on
  /status as persistence state, but never fail the API call.

Provenance note: this file is phase-3 original work (Luna, 2026-10-02);
phases 1-2 history lives in the repo commits.
"""
import json
import logging
from datetime import datetime
from typing import Optional

import asyncpg

from config import DATABASE_URL

logger = logging.getLogger(__name__)


def pg_url() -> str:
    """DATABASE_URL in a form asyncpg accepts (no SQLAlchemy driver suffix)."""
    return DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")


class Persistence:
    """Write-through PostgreSQL persistence for the Store.

    The pool is created lazily inside whichever event loop first uses it,
    so the object is loop-agnostic (uvicorn server loop, test portal loop,
    or a script's asyncio.run loop all work).
    """

    def __init__(self, url: str):
        self.url = url
        self._pool: Optional[asyncpg.Pool] = None
        self.last_error: Optional[str] = None
        self.writes_ok = 0
        self.writes_failed = 0

    @property
    def pool(self):
        return self._pool

    def state(self) -> dict:
        s = {
            "kind": "PostgreSQL (asyncpg, write-through)",
            "writes_ok": self.writes_ok,
            "writes_failed": self.writes_failed,
        }
        if self.last_error:
            s["last_error"] = self.last_error
        return s

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.url, min_size=1,
                                                   max_size=5, command_timeout=5)
        return self._pool

    async def _run(self, sql: str, *args) -> bool:
        try:
            pool = await self._get_pool()
            await pool.execute(sql, *args)
            self.last_error = None
            self.writes_ok += 1
            return True
        except Exception as e:  # never fail the API call on persistence trouble
            msg = f"{type(e).__name__}: {e}"
            # A pool created in one event loop cannot serve another; rebuild
            # it in the current loop and retry once.
            if self._pool is not None and ("attached to a different loop" in str(e)
                                           or "not bound to a loop" in str(e)):
                try:
                    await self._pool.close()
                except Exception:
                    pass
                self._pool = None
                try:
                    pool = await self._get_pool()
                    await pool.execute(sql, *args)
                    self.last_error = None
                    self.writes_ok += 1
                    return True
                except Exception as e2:
                    msg = f"{type(e2).__name__}: {e2}"
            self.last_error = msg
            self.writes_failed += 1
            logger.warning("persistence write failed: %s", self.last_error)
            return False

    async def save_ship(self, s) -> bool:
        return await self._run(
            """INSERT INTO ships (id, call_sign, name, ship_type, gross_tonnage,
                                   crew_count, home_port, created_at, updated_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
               ON CONFLICT (id) DO UPDATE SET call_sign=EXCLUDED.call_sign,
                   name=EXCLUDED.name, ship_type=EXCLUDED.ship_type,
                   gross_tonnage=EXCLUDED.gross_tonnage, crew_count=EXCLUDED.crew_count,
                   home_port=EXCLUDED.home_port, updated_at=EXCLUDED.updated_at""",
            s.id, s.call_sign, s.name, s.ship_type, s.gross_tonnage,
            s.crew_count, s.home_port, s.created_at, s.updated_at,
        )

    async def save_crew(self, c) -> bool:
        return await self._run(
            """INSERT INTO crew (id, ship_id, name, role, employee_id,
                                 contact_info, certification_level, created_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
               ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, role=EXCLUDED.role,
                   employee_id=EXCLUDED.employee_id, contact_info=EXCLUDED.contact_info,
                   certification_level=EXCLUDED.certification_level""",
            c.id, c.ship_id, c.name, c.role, c.employee_id,
            c.contact_info, c.certification_level, c.created_at,
        )

    async def save_decision(self, d) -> bool:
        return await self._run(
            """INSERT INTO decisions (id, ship_id, decision_type, decision_maker,
                    recommended_action, reasoning, confidence_score, status,
                    approver_id, approval_notes, created_at, decided_at, executed_at)
               VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
               ON CONFLICT (id) DO UPDATE SET status=EXCLUDED.status,
                   approver_id=EXCLUDED.approver_id, approval_notes=EXCLUDED.approval_notes,
                   decided_at=EXCLUDED.decided_at, executed_at=EXCLUDED.executed_at""",
            d.id, d.ship_id, d.decision_type, d.decision_maker,
            d.recommended_action, json.dumps(d.reasoning), d.confidence_score, d.status,
            d.approver_id, d.approval_notes, d.created_at, d.decided_at, d.executed_at,
        )

    async def save_telemetry(self, ship_id: int, record: dict) -> bool:
        return await self._run(
            """INSERT INTO telemetry (ship_id, payload, recorded_at)
               VALUES ($1,$2,$3)""",
            ship_id, json.dumps(record), self._ts(record.get("timestamp")),
        )

    async def save_notification(self, crew_id: int, notification: dict) -> bool:
        return await self._run(
            """INSERT INTO notifications (crew_id, payload, created_at)
               VALUES ($1,$2,$3)""",
            crew_id, json.dumps(notification), self._ts(notification.get("created_at")),
        )

    @staticmethod
    def _ts(value):
        """ISO string -> datetime for TIMESTAMPTZ params (asyncpg is strict)."""
        if value is None or isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return None


DDL = """
CREATE TABLE IF NOT EXISTS ships (
    id BIGINT PRIMARY KEY,
    call_sign TEXT NOT NULL,
    name TEXT NOT NULL,
    ship_type TEXT,
    gross_tonnage DOUBLE PRECISION,
    crew_count INTEGER DEFAULT 0,
    home_port TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS crew (
    id BIGINT PRIMARY KEY,
    ship_id BIGINT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    contact_info TEXT,
    certification_level TEXT,
    created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id BIGINT PRIMARY KEY,
    ship_id BIGINT REFERENCES ships(id) ON DELETE CASCADE,
    decision_type TEXT NOT NULL,
    decision_maker TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    reasoning JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence_score DOUBLE PRECISION,
    status TEXT NOT NULL DEFAULT 'pending_approval',
    approver_id BIGINT,
    approval_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    decided_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    ship_id BIGINT NOT NULL REFERENCES ships(id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    recorded_at TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS notifications (
    id BIGSERIAL PRIMARY KEY,
    crew_id BIGINT NOT NULL REFERENCES crew(id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ
);
"""


async def connect() -> Optional[asyncpg.Pool]:
    """Open a pool, or return None if Postgres is unreachable."""
    try:
        return await asyncpg.create_pool(pg_url(), min_size=1, max_size=5,
                                         command_timeout=5)
    except Exception as e:
        logger.warning("PostgreSQL connect failed: %s", e)
        return None


async def bootstrap(pool: asyncpg.Pool):
    await pool.execute(DDL)


async def hydrate(pool: asyncpg.Pool, store) -> dict:
    """Load persisted rows back into the Store and fix id sequences.

    Returns counts for /status. Called at startup BEFORE the API serves.
    """
    counts = {}
    async with pool.acquire() as conn:
        for row in await conn.fetch("SELECT * FROM ships ORDER BY id"):
            store.ships[row["id"]] = store.ShipClass(
                id=row["id"], call_sign=row["call_sign"], name=row["name"],
                ship_type=row["ship_type"], gross_tonnage=row["gross_tonnage"],
                crew_count=row["crew_count"], home_port=row["home_port"],
                created_at=row["created_at"], updated_at=row["updated_at"],
            )
        counts["ships"] = len(store.ships)

        for row in await conn.fetch("SELECT * FROM crew ORDER BY id"):
            store.crew[row["id"]] = store.CrewClass(
                id=row["id"], ship_id=row["ship_id"], name=row["name"],
                role=row["role"], employee_id=row["employee_id"],
                contact_info=row["contact_info"],
                certification_level=row["certification_level"],
                created_at=row["created_at"],
            )
        counts["crew"] = len(store.crew)

        for row in await conn.fetch("SELECT * FROM decisions ORDER BY id"):
            store.decisions[row["id"]] = store.DecisionClass(
                id=row["id"], ship_id=row["ship_id"],
                decision_type=row["decision_type"],
                decision_maker=row["decision_maker"],
                recommended_action=row["recommended_action"],
                reasoning=json.loads(row["reasoning"]),
                confidence_score=row["confidence_score"],
                status=row["status"], approver_id=row["approver_id"],
                approval_notes=row["approval_notes"],
                created_at=row["created_at"], decided_at=row["decided_at"],
                executed_at=row["executed_at"],
            )
        counts["decisions"] = len(store.decisions)

        for row in await conn.fetch("SELECT * FROM telemetry ORDER BY id"):
            store.telemetry.setdefault(row["ship_id"], []).append(
                json.loads(row["payload"]))
        counts["telemetry_points"] = sum(len(v) for v in store.telemetry.values())

        for row in await conn.fetch("SELECT * FROM notifications ORDER BY id"):
            store.notifications.setdefault(row["crew_id"], []).append(
                json.loads(row["payload"]))
        counts["notifications"] = sum(len(v) for v in store.notifications.values())

    if store.ships:
        store._ship_seq = max(store.ships)
    if store.crew:
        store._crew_seq = max(store.crew)
    if store.decisions:
        store._decision_seq = max(store.decisions)
    return counts


async def close(pool: Optional[asyncpg.Pool]):
    if pool is not None:
        await pool.close()
