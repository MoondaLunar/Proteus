# Phase 3 Summary — PostgreSQL Persistence (2026-10-03)

Phase 2 made the API real on an in-process store. Phase 3 makes the store
survive restarts: write-through to PostgreSQL via asyncpg, hydration on
startup. The API never depends on Postgres being reachable — when it is
down, the API still serves from memory and /status says so.

## What's new

- **`persistence.py`** (new): asyncpg write-through layer.
  - `Persistence` opens its pool lazily in whichever event loop first uses
    it, so the same object works under uvicorn, TestClient portals, and
    scripts. A pool created in the wrong loop is detected and rebuilt.
  - Schema bootstrapped idempotently (CREATE TABLE IF NOT EXISTS) for
    ships, crew, decisions, telemetry, notifications.
  - `hydrate()` reloads rows into the Store and fixes id sequences.
  - Every write is best-effort: failures are counted on /status
    (`persistence.writes_failed`, `last_error`), never fail the API call.
  - ISO-string timestamps are converted to datetimes (asyncpg is strict
    about TIMESTAMPTZ parameters).

- **`main.py`**: `setup_persistence()` (idempotent, callable directly),
  called from the lifespan before serving; pool closed on shutdown.
  `/status` now reports a `persistence` block:
  `PostgreSQL (asyncpg, write-through)` with write counters, or
  `in-memory only (...)` when Postgres is unreachable.

- **Write-through hooks** in `ships.py`, `crew.py`, `telemetry.py`,
  `decisions.py`: create/approve/execute/telemetry/notification writes are
  persisted after the in-memory mutation (under the same ordering).

## Verified

- `pytest conftest.py -q`: **25/25 pass** (24 phase-2 tests unchanged, plus
  1 phase-3 integration test).
- The phase-3 test runs a **real uvicorn server twice**: server 1 registers
  a ship, crew member, telemetry point, and a decision approved through the
  lifecycle (all writes land in Postgres, `writes_failed == 0`); the server
  is killed; server 2 starts fresh, hydrates from Postgres, and verifies
  every record survived and the id sequences continue.

## Honest limits

- Tokens are still in-memory only (auth tokens are ephemeral by design).
- Single-node: no multi-instance coordination; two servers against one DB
  would diverge in-memory state.
- No migrations framework yet; schema is bootstrap-on-start.
