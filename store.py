"""
In-memory store for Maritime AI System (phase 2, made real 2026-09-30)

This is real working storage, not a stub: ships, crew, telemetry, decisions,
auth tokens, an ingest message queue, and a TTL cache. It is explicitly
IN-MEMORY: data lives for the life of the process and is lost on restart.
Persistence to PostgreSQL awaits a reachable database (see database.py).
The /status endpoint reports this honestly.

Thread safety: all mutations go through a single asyncio.Lock, so concurrent
FastAPI handlers cannot corrupt state.
"""
import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Any

from config import ACCESS_TOKEN_EXPIRE_MINUTES


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Ship:
    id: int
    call_sign: str
    name: str
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    crew_count: int = 0
    home_port: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass
class CrewMember:
    id: int
    ship_id: int
    name: str
    role: str
    employee_id: str
    contact_info: Optional[str] = None
    certification_level: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)


@dataclass
class Decision:
    id: int
    ship_id: Optional[int]
    decision_type: str
    decision_maker: str
    recommended_action: str
    reasoning: dict
    confidence_score: Optional[float]
    status: str = "pending_approval"  # pending_approval | approved | rejected | executed
    approver_id: Optional[int] = None
    approval_notes: Optional[str] = None
    created_at: datetime = field(default_factory=utcnow)
    decided_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None


@dataclass
class AuthToken:
    token: str
    crew_id: int
    expires_at: float  # time.monotonic-based expiry


class Store:
    """Process-lifetime state for the whole API."""

    def __init__(self):
        self.lock = asyncio.Lock()
        # Phase 3: optional write-through persistence (None = in-memory only).
        self.persist = None
        # Class references used by persistence.hydrate()
        self.ShipClass = Ship
        self.CrewClass = CrewMember
        self.DecisionClass = Decision
        self.ships: dict[int, Ship] = {}
        self.crew: dict[int, CrewMember] = {}
        self.decisions: dict[int, Decision] = {}
        self.telemetry: dict[int, list[dict]] = {}   # ship_id -> newest-last
        self.tokens: dict[str, AuthToken] = {}
        self.notifications: dict[int, list[dict]] = {}  # crew_id -> newest-last
        self._ship_seq = 0
        self._crew_seq = 0
        self._decision_seq = 0
        self.queue = IngestQueue()
        self.cache = TTLCache(default_ttl_seconds=30)

    # ---- ships ----
    def next_ship_id(self) -> int:
        self._ship_seq += 1
        return self._ship_seq

    def next_crew_id(self) -> int:
        self._crew_seq += 1
        return self._crew_seq

    def next_decision_id(self) -> int:
        self._decision_seq += 1
        return self._decision_seq

    # ---- auth ----
    def issue_token(self, crew_id: int) -> AuthToken:
        import secrets
        tok = AuthToken(
            token=secrets.token_urlsafe(32),
            crew_id=crew_id,
            expires_at=time.monotonic() + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        self.tokens[tok.token] = tok
        return tok

    def token_valid(self, token: str) -> bool:
        tok = self.tokens.get(token)
        return tok is not None and tok.expires_at > time.monotonic()


class IngestQueue:
    """Minimal in-process message queue for telemetry ingestion events.

    Producers put events; a consumer drains them. Depth is reported on
    /status. Not a RabbitMQ replacement; it removes the fake claim that
    queueing exists elsewhere.
    """

    def __init__(self, maxsize: int = 1000):
        self.q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self.total_enqueued = 0
        self.total_consumed = 0

    def enqueue(self, event: dict) -> bool:
        try:
            self.q.put_nowait(event)
            self.total_enqueued += 1
            return True
        except asyncio.QueueFull:
            return False

    def drain(self, max_items: int = 100) -> list[dict]:
        out = []
        while len(out) < max_items:
            try:
                out.append(self.q.get_nowait())
                self.total_consumed += 1
            except asyncio.QueueEmpty:
                break
        return out

    def state(self) -> dict:
        return {
            "depth": self.q.qsize(),
            "total_enqueued": self.total_enqueued,
            "total_consumed": self.total_consumed,
            "kind": "in-process (not RabbitMQ)",
        }


class TTLCache:
    """Simple TTL cache for read responses. Entries expire; nothing fancy."""

    def __init__(self, default_ttl_seconds: float = 30, maxsize: int = 500):
        self.data: dict[str, tuple[float, Any]] = {}
        self.default_ttl = default_ttl_seconds
        self.maxsize = maxsize
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        entry = self.data.get(key)
        if entry is None:
            self.misses += 1
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            del self.data[key]
            self.misses += 1
            return None
        self.hits += 1
        return value

    def put(self, key: str, value: Any, ttl_seconds: Optional[float] = None):
        if len(self.data) >= self.maxsize:
            # Drop the oldest entry (insertion order).
            oldest = next(iter(self.data))
            del self.data[oldest]
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self.data[key] = (time.monotonic() + ttl, value)

    def invalidate(self, prefix: str):
        for key in [k for k in self.data if k.startswith(prefix)]:
            del self.data[key]

    def state(self) -> dict:
        return {
            "entries": len(self.data),
            "hits": self.hits,
            "misses": self.misses,
            "default_ttl_seconds": self.default_ttl,
            "kind": "in-process TTL (not Redis)",
        }


store = Store()

