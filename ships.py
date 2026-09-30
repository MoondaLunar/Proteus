"""
Ships Management Routes
Handles ship registration, status, and configuration.
Phase 2 (2026-09-30): backed by the in-memory store; reads cached with TTL.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from store import store

router = APIRouter()

# Models
class ShipCreate(BaseModel):
    call_sign: str
    name: str
    ship_type: Optional[str] = None
    gross_tonnage: Optional[float] = None
    crew_count: Optional[int] = None
    home_port: Optional[str] = None


def _ship_summary(ship) -> dict:
    return {
        "id": ship.id,
        "call_sign": ship.call_sign,
        "name": ship.name,
        "ship_type": ship.ship_type,
        "crew_count": ship.crew_count,
        "home_port": ship.home_port,
        "created_at": ship.created_at.isoformat(),
        "updated_at": ship.updated_at.isoformat(),
    }


def _ship_or_404(ship_id: int):
    ship = store.ships.get(ship_id)
    if ship is None:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    return ship


@router.get("/ships")
async def list_ships(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """List all registered ships (paginated, from the store)"""
    ships = sorted(store.ships.values(), key=lambda s: s.id)
    page = ships[skip : skip + limit]
    return {
        "ships": [_ship_summary(s) for s in page],
        "total_count": len(ships),
        "skip": skip,
        "limit": limit,
        "storage": "in-memory",
    }


@router.post("/ships", status_code=201)
async def register_ship(ship: ShipCreate):
    """Register a new ship in the store"""
    async with store.lock:
        if any(s.call_sign == ship.call_sign for s in store.ships.values()):
            raise HTTPException(status_code=409, detail=f"Call sign {ship.call_sign} already registered")
        from store import Ship as ShipModel
        rec = ShipModel(
            id=store.next_ship_id(),
            call_sign=ship.call_sign,
            name=ship.name,
            ship_type=ship.ship_type,
            gross_tonnage=ship.gross_tonnage,
            crew_count=ship.crew_count or 0,
            home_port=ship.home_port,
        )
        store.ships[rec.id] = rec
        store.cache.invalidate("ships")
    store.queue.enqueue({"event": "ship_registered", "ship_id": rec.id, "at": utcnow_iso()})
    return {"ship": _ship_summary(rec), "status": "created", "storage": "in-memory"}


def utcnow_iso() -> str:
    from store import utcnow
    return utcnow().isoformat()


@router.get("/ships/{ship_id}")
async def get_ship_details(ship_id: int):
    """Detailed information about a specific ship (cached read)"""
    key = f"ships:{ship_id}"
    cached = store.cache.get(key)
    if cached is not None:
        return cached
    ship = _ship_or_404(ship_id)
    detail = _ship_summary(ship)
    detail["telemetry_points"] = len(store.telemetry.get(ship_id, []))
    detail["crew_ids"] = [c.id for c in store.crew.values() if c.ship_id == ship_id]
    store.cache.put(key, detail)
    return detail


@router.get("/ships/{ship_id}/status")
async def get_ship_status(ship_id: int):
    """Real-time status of a ship, derived from ingested telemetry"""
    _ship_or_404(ship_id)
    tel = store.telemetry.get(ship_id, [])
    latest_gps = next((t for t in reversed(tel) if t["sensor_type"] == "gps"), None)
    gps = latest_gps["data_point"] if latest_gps else {"latitude": 0.0, "longitude": 0.0}
    return {
        "ship_id": ship_id,
        "status": "operational",
        "gps": gps,
        "crew_count": sum(1 for c in store.crew.values() if c.ship_id == ship_id),
        "telemetry_points": len(tel),
        "last_update": max((t["ingested_at"] for t in tel), default=None),
        "note": "status derived from in-memory telemetry only",
    }


@router.get("/ships/{ship_id}/power")
async def get_power_status(ship_id: int):
    """Power system status: latest battery telemetry if ingested, else defaults"""
    _ship_or_404(ship_id)
    tel = store.telemetry.get(ship_id, [])
    latest = next((t for t in reversed(tel) if t["sensor_type"] == "battery"), None)
    if latest:
        charge = latest["data_point"].get("battery_percent")
        capacity = latest["data_point"].get("total_capacity_kwh", 500)
    else:
        charge, capacity = 0, 500
    return {
        "ship_id": ship_id,
        "battery_percent": charge,
        "total_capacity_kwh": capacity,
        "source": "telemetry" if latest else "defaults (no battery telemetry ingested)",
    }


@router.get("/ships/{ship_id}/sensors")
async def get_ship_sensors(ship_id: int):
    """Sensor types seen in ingested telemetry for this ship"""
    _ship_or_404(ship_id)
    tel = store.telemetry.get(ship_id, [])
    types = sorted({t["sensor_type"] for t in tel})
    return {
        "ship_id": ship_id,
        "sensors": types,
        "active_count": len(types),
        "inactive_count": 0,
        "note": "derived from telemetry ingested this process run",
    }

