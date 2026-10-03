"""
Telemetry and Sensor Data Routes
Real-time sensor data ingestion and retrieval.
Phase 2 (2026-09-30): ingest enqueues to the in-process queue and stores
newest-last; reads serve from the store.
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from store import store, utcnow

router = APIRouter()


class TelemetryData(BaseModel):
    sensor_type: str
    data_point: dict
    timestamp: Optional[datetime] = None


class GPSPosition(BaseModel):
    latitude: float
    longitude: float
    heading: Optional[float] = None
    speed_knots: Optional[float] = None
    accuracy_m: Optional[float] = None


class WeatherReading(BaseModel):
    wind_speed_knots: float
    wind_direction_deg: float
    wave_height_m: float
    temperature_c: float
    barometric_pressure_mb: float
    visibility_nm: Optional[float] = None


def _ship_or_404(ship_id: int):
    if ship_id not in store.ships:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    return store.ships[ship_id]


def _latest(ship_id: int, sensor_type: str) -> Optional[dict]:
    tel = store.telemetry.get(ship_id, [])
    return next((t for t in reversed(tel) if t["sensor_type"] == sensor_type), None)


@router.get("/telemetry/{ship_id}")
async def get_telemetry_data(ship_id: int, limit: int = 100):
    """Recent telemetry for a ship (newest-last, from the store)"""
    _ship_or_404(ship_id)
    tel = store.telemetry.get(ship_id, [])[-limit:]
    latest_update = max((t["ingested_at"] for t in tel), default=None)
    return {
        "ship_id": ship_id,
        "telemetry": tel,
        "count": len(tel),
        "latest_update": latest_update,
        "storage": "in-memory",
    }


@router.post("/telemetry/{ship_id}", status_code=202)
async def ingest_telemetry(ship_id: int, telemetry: TelemetryData):
    """Ingest sensor data from a ship: store it, then enqueue the event"""
    _ship_or_404(ship_id)
    record = {
        "sensor_type": telemetry.sensor_type,
        "data_point": telemetry.data_point,
        "timestamp": (telemetry.timestamp or utcnow()).isoformat(),
        "ingested_at": utcnow().isoformat(),
    }
    async with store.lock:
        store.telemetry.setdefault(ship_id, []).append(record)
        store.cache.invalidate(f"ships:{ship_id}")
    if store.persist:
        await store.persist.save_telemetry(ship_id, record)
    queued = store.queue.enqueue({"event": "telemetry", "ship_id": ship_id, "sensor_type": telemetry.sensor_type})
    return {
        "ship_id": ship_id,
        "status": "received",
        "queued": queued,
        "points_stored": len(store.telemetry[ship_id]),
    }


@router.get("/telemetry/{ship_id}/gps")
async def get_current_position(ship_id: int):
    """Current GPS position: last ingested gps reading, else nulls"""
    _ship_or_404(ship_id)
    latest = _latest(ship_id, "gps")
    if latest:
        gps = {**latest["data_point"], "timestamp": latest["ingested_at"]}
    else:
        gps = {"latitude": None, "longitude": None, "heading_deg": None, "speed_knots": None, "timestamp": None}
    return {"ship_id": ship_id, "gps": gps, "source": "telemetry" if latest else "no gps ingested yet"}


@router.post("/telemetry/{ship_id}/gps", status_code=202)
async def update_gps_position(ship_id: int, position: GPSPosition):
    """Update GPS position (stored as a gps telemetry point)"""
    _ship_or_404(ship_id)
    record = {
        "sensor_type": "gps",
        "data_point": {
            "latitude": position.latitude,
            "longitude": position.longitude,
            "heading_deg": position.heading,
            "speed_knots": position.speed_knots,
            "accuracy_m": position.accuracy_m,
        },
        "timestamp": utcnow().isoformat(),
        "ingested_at": utcnow().isoformat(),
    }
    async with store.lock:
        store.telemetry.setdefault(ship_id, []).append(record)
        store.cache.invalidate(f"ships:{ship_id}")
    if store.persist:
        await store.persist.save_telemetry(ship_id, record)
    return {"ship_id": ship_id, "position": record["data_point"], "status": "updated"}


@router.get("/telemetry/{ship_id}/weather")
async def get_weather_data(ship_id: int):
    """Current weather: last ingested weather reading, else nulls"""
    _ship_or_404(ship_id)
    latest = _latest(ship_id, "weather")
    if latest:
        weather = {**latest["data_point"], "timestamp": latest["ingested_at"]}
        source = "telemetry"
    else:
        weather = {"timestamp": None}
        source = "no weather ingested yet"
    return {"ship_id": ship_id, "weather": weather, "source": source}


@router.post("/telemetry/{ship_id}/weather", status_code=202)
async def ingest_weather_data(ship_id: int, weather: WeatherReading):
    """Ingest weather sensor data"""
    _ship_or_404(ship_id)
    record = {
        "sensor_type": "weather",
        "data_point": weather.model_dump(),
        "timestamp": utcnow().isoformat(),
        "ingested_at": utcnow().isoformat(),
    }
    async with store.lock:
        store.telemetry.setdefault(ship_id, []).append(record)
    queued = store.queue.enqueue({"event": "weather", "ship_id": ship_id})
    return {"ship_id": ship_id, "status": "received", "queued": queued}


@router.get("/telemetry/{ship_id}/radar")
async def get_radar_data(ship_id: int):
    """Radar contacts: last ingested radar reading, else empty"""
    _ship_or_404(ship_id)
    latest = _latest(ship_id, "radar")
    return {
        "ship_id": ship_id,
        "radar_active": latest is not None,
        "contacts": latest["data_point"].get("contacts", []) if latest else [],
        "contact_count": len(latest["data_point"].get("contacts", [])) if latest else 0,
        "timestamp": latest["ingested_at"] if latest else None,
        "source": "telemetry" if latest else "no radar ingested yet",
    }


@router.get("/telemetry/{ship_id}/power")
async def get_power_data(ship_id: int):
    """Renewable power telemetry: latest battery reading, else nulls"""
    _ship_or_404(ship_id)
    latest = _latest(ship_id, "battery")
    if latest:
        dp = latest["data_point"]
        battery = {
            "capacity_kwh": dp.get("total_capacity_kwh"),
            "current_charge_kwh": dp.get("battery_charge_kwh"),
            "charge_percent": dp.get("battery_percent"),
        }
    else:
        battery = {"capacity_kwh": None, "current_charge_kwh": None, "charge_percent": None}
    return {
        "ship_id": ship_id,
        "battery": battery,
        "timestamp": latest["ingested_at"] if latest else None,
        "source": "telemetry" if latest else "no battery telemetry ingested yet",
    }


@router.get("/telemetry/{ship_id}/radio")
async def get_radio_data(ship_id: int):
    """Monitored radio communications: latest radio reading, else empty"""
    _ship_or_404(ship_id)
    latest = _latest(ship_id, "radio")
    return {
        "ship_id": ship_id,
        "monitoring_active": latest is not None,
        "recent_communications": latest["data_point"].get("communications", []) if latest else [],
        "communication_count": len(latest["data_point"].get("communications", [])) if latest else 0,
        "timestamp": latest["ingested_at"] if latest else None,
        "source": "telemetry" if latest else "no radio ingested yet",
    }

