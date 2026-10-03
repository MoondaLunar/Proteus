"""
Crew Management and Communication Routes
Crew authentication, communication, and notification management.
Phase 2 (2026-09-30): real crew records, honest tokens, queued notifications.

Route disambiguation (was a seam in the skeleton): the list route keeps
/crew/{ship_id}; crew profiles moved to /crew/member/{crew_id} so the two
same-shaped paths can no longer shadow each other.
"""
from fastapi import APIRouter, HTTPException, Query
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone

from store import store

router = APIRouter()


class CrewRole(str, Enum):
    CAPTAIN = "Captain"
    FIRST_MATE = "First Mate"
    ENGINEER = "Engineer"
    NAVIGATOR = "Navigator"
    DECKHAND = "Deckhand"
    SUPPORT = "Support"


class CrewCreate(BaseModel):
    name: str
    role: CrewRole
    employee_id: str
    contact_info: Optional[str] = None
    certification_level: Optional[str] = None


class CrewAuthentication(BaseModel):
    username: str
    password: str


class CrewCommunication(BaseModel):
    message_type: str
    content: str
    priority: Optional[str] = "normal"
    recipient_ids: Optional[List[int]] = None


def _crew_or_404(crew_id: int):
    c = store.crew.get(crew_id)
    if c is None:
        raise HTTPException(status_code=404, detail=f"Crew member {crew_id} not found")
    return c


def _crew_out(c) -> dict:
    return {
        "id": c.id,
        "ship_id": c.ship_id,
        "name": c.name,
        "role": c.role,
        "employee_id": c.employee_id,
        "contact_info": c.contact_info,
        "certification_level": c.certification_level,
        "created_at": c.created_at.isoformat(),
    }


@router.get("/crew/{ship_id}")
async def list_crew(ship_id: int):
    """List all crew members on a ship (from the store)"""
    if ship_id not in store.ships:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    members = [c for c in store.crew.values() if c.ship_id == ship_id]
    return {
        "ship_id": ship_id,
        "crew_members": [_crew_out(c) for c in members],
        "total_count": len(members),
        "active_count": len(members),
        "storage": "in-memory",
    }


@router.post("/crew/{ship_id}", status_code=201)
async def add_crew_member(ship_id: int, crew: CrewCreate):
    """Add a crew member to a ship"""
    if ship_id not in store.ships:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    async with store.lock:
        from store import CrewMember
        member = CrewMember(
            id=store.next_crew_id(),
            ship_id=ship_id,
            name=crew.name,
            role=crew.role.value,
            employee_id=crew.employee_id,
            contact_info=crew.contact_info,
            certification_level=crew.certification_level,
        )
        store.crew[member.id] = member
        ship = store.ships[ship_id]
        ship.crew_count += 1
        ship.updated_at = datetime.now(timezone.utc)
        store.cache.invalidate(f"ships:{ship_id}")
    if store.persist:
        await store.persist.save_crew(member)
        await store.persist.save_ship(ship)
    return {"crew_member": _crew_out(member), "status": "created"}


@router.get("/crew/member/{crew_id}")
async def get_crew_profile(crew_id: int):
    """Crew member profile (disambiguated route)"""
    c = _crew_or_404(crew_id)
    profile = _crew_out(c)
    profile["years_experience"] = 0
    profile["certifications"] = [c.certification_level] if c.certification_level else []
    return profile


@router.post("/crew/{crew_id}/authenticate")
async def authenticate_crew(crew_id: int, auth: CrewAuthentication):
    """Authenticate crew member and return an API token.

    Honest scope: this checks the crew record exists and issues a real
    random token with expiry, tracked in the store. It is not production
    auth; there is no password store yet.
    """
    c = _crew_or_404(crew_id)
    token = store.issue_token(crew_id)
    from config import ACCESS_TOKEN_EXPIRE_MINUTES
    return {
        "crew_id": crew_id,
        "authenticated": True,
        "token": token.token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": "demo auth: token tracked in-memory, no password store",
    }


@router.post("/crew/{crew_id}/comms")
async def send_crew_communication(crew_id: int, comms: CrewCommunication):
    """Send communication to a crew member: queued as a notification"""
    c = _crew_or_404(crew_id)
    recipients = comms.recipient_ids or [crew_id]
    delivered = []
    for rid in recipients:
        if rid not in store.crew:
            raise HTTPException(status_code=404, detail=f"Crew member {rid} not found")
    async with store.lock:
        for rid in recipients:
            note = {
                "id": len(store.notifications.get(rid, [])) + 1,
                "from_crew_id": crew_id,
                "message_type": comms.message_type,
                "content": comms.content,
                "priority": comms.priority,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "read": False,
            }
            store.notifications.setdefault(rid, []).append(note)
            delivered.append(rid)
    if store.persist:
        for rid in delivered:
            note = store.notifications[rid][-1]
            await store.persist.save_notification(rid, note)
    store.queue.enqueue({"event": "crew_comm", "recipients": delivered})
    return {"from_crew_id": crew_id, "delivered_to": delivered, "status": "sent"}


@router.get("/crew/{crew_id}/notifications")
async def get_notifications(crew_id: int, unread_only: bool = True):
    """Crew member notifications (real, from the store)"""
    c = _crew_or_404(crew_id)
    notes = store.notifications.get(crew_id, [])
    shown = [n for n in notes if not n["read"]] if unread_only else notes
    return {
        "crew_id": crew_id,
        "notifications": shown,
        "unread_count": sum(1 for n in notes if not n["read"]),
        "total_count": len(notes),
    }


@router.get("/crew/{crew_id}/preferences")
async def get_communication_preferences(crew_id: int):
    """Communication preferences (defaults until a PUT is issued)"""
    c = _crew_or_404(crew_id)
    prefs = store.cache.get(f"crew_prefs:{crew_id}")
    if prefs is None:
        prefs = {
            "notification_method": "push",
            "alert_level": "warning",
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00",
            "language": "en",
        }
    return {"crew_id": crew_id, **prefs, "source": "defaults" if store.cache.get(f"crew_prefs:{crew_id}") is None else "updated"}


@router.put("/crew/{crew_id}/preferences")
async def update_communication_preferences(crew_id: int, preferences: dict):
    """Update communication preferences (stored via the cache layer)"""
    c = _crew_or_404(crew_id)
    allowed = {"notification_method", "alert_level", "quiet_hours_start", "quiet_hours_end", "language"}
    cleaned = {k: v for k, v in preferences.items() if k in allowed}
    store.cache.put(f"crew_prefs:{crew_id}", cleaned, ttl_seconds=86400)
    return {"crew_id": crew_id, "preferences": cleaned, "status": "updated"}


@router.get("/crew/{ship_id}/captain")
async def get_ship_captain(ship_id: int):
    """The captain of a ship (first Captain-role member found)"""
    if ship_id not in store.ships:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    captain = next((c for c in store.crew.values() if c.ship_id == ship_id and c.role == "Captain"), None)
    return {"ship_id": ship_id, "captain": _crew_out(captain) if captain else None}


@router.get("/crew/{ship_id}/decision-log")
async def get_crew_decision_log(ship_id: int, crew_id: Optional[int] = None, days: int = Query(7, ge=1, le=365)):
    """Decision log for a crew member (from the decisions store)"""
    if ship_id not in store.ships:
        raise HTTPException(status_code=404, detail=f"Ship {ship_id} not found")
    from decisions import _decision_out
    items = [d for d in store.decisions.values() if d.ship_id == ship_id]
    if crew_id is not None:
        # decisions store does not yet track originating crew_id; say so honestly
        pass
    return {
        "ship_id": ship_id,
        "crew_id": crew_id,
        "period_days": days,
        "decisions": [_decision_out(d) for d in items],
        "total_count": len(items),
        "note": "originating crew_id not yet tracked on decisions",
    }


@router.post("/crew/{crew_id}/acknowledge")
async def acknowledge_decision(crew_id: int, decision_id: int = Query(..., description="ID of the decision being acknowledged")):
    """Crew acknowledges receipt of a decision notification"""
    c = _crew_or_404(crew_id)
    if decision_id not in store.decisions:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    ts = datetime.now(timezone.utc).isoformat()
    store.queue.enqueue({"event": "decision_acknowledged", "crew_id": crew_id, "decision_id": decision_id})
    return {"crew_id": crew_id, "decision_id": decision_id, "acknowledged": True, "timestamp": ts}

