"""
Decisions and AI Recommendations Routes
Core intelligence endpoints for decision logging and captain interaction.
Phase 2 (2026-09-30): real decision lifecycle on the in-memory store.

Route ordering: the literal /decisions/pending and /decisions/history are
declared BEFORE /decisions/{decision_id} so they can't be shadowed by it.
"""
from fastapi import APIRouter, HTTPException, Query
from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from store import store, Decision

router = APIRouter()


class DecisionMaker(str, Enum):
    AI_SYSTEM = "ai_system"
    CAPTAIN = "captain"
    FIRST_MATE = "first_mate"


class DecisionType(str, Enum):
    HEADING_CHANGE = "heading_change"
    SPEED_ADJUSTMENT = "speed_adjustment"
    ROUTE_CHANGE = "route_change"
    WEATHER_AVOIDANCE = "weather_avoidance"
    EMERGENCY = "emergency"


class DecisionCreate(BaseModel):
    ship_id: Optional[int] = None
    decision_type: DecisionType
    decision_maker: DecisionMaker
    recommended_action: str
    reasoning: dict = {}
    confidence_score: Optional[float] = None


class DecisionApproval(BaseModel):
    approved: bool
    approver_id: int
    notes: Optional[str] = None


def _decision_out(d) -> dict:
    return {
        "id": d.id,
        "ship_id": d.ship_id,
        "decision_type": d.decision_type,
        "decision_maker": d.decision_maker,
        "recommended_action": d.recommended_action,
        "reasoning": d.reasoning,
        "confidence_score": d.confidence_score,
        "status": d.status,
        "approver_id": d.approver_id,
        "approval_notes": d.approval_notes,
        "created_at": d.created_at.isoformat(),
        "decided_at": d.decided_at.isoformat() if d.decided_at else None,
        "executed_at": d.executed_at.isoformat() if d.executed_at else None,
    }


def _decision_or_404(decision_id: int) -> Decision:
    d = store.decisions.get(decision_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    return d


# --- literal routes first (they'd otherwise be shadowed by /{decision_id}) ---

@router.get("/decisions/pending")
async def get_pending_decisions(ship_id: Optional[int] = Query(None)):
    """All pending decisions awaiting approval"""
    items = [d for d in store.decisions.values() if d.status == "pending_approval"]
    if ship_id is not None:
        items = [d for d in items if d.ship_id == ship_id]
    return {"pending_decisions": [_decision_out(d) for d in items], "count": len(items)}


@router.get("/decisions/history")
async def get_decision_history(
    ship_id: int = Query(...),
    days: int = Query(7, ge=1, le=365),
):
    """Decision history for a ship"""
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    items = [
        d for d in store.decisions.values()
        if d.ship_id == ship_id and d.created_at.timestamp() >= cutoff
    ]
    ai = sum(1 for d in items if d.decision_maker == "ai_system")
    cap = sum(1 for d in items if d.decision_maker == "captain")
    accepted = sum(1 for d in items if d.decision_maker == "ai_system" and d.status in ("approved", "executed"))
    return {
        "ship_id": ship_id,
        "period_days": days,
        "decisions": [_decision_out(d) for d in items],
        "total_ai_decisions": ai,
        "total_captain_decisions": cap,
        "ai_acceptance_rate": (accepted / ai) if ai else 0.0,
        "storage": "in-memory",
    }


# --- parameterized routes ---

@router.get("/decisions")
async def list_decisions(
    ship_id: Optional[int] = Query(None),
    decision_maker: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List decisions with filtering (from the store)"""
    items = sorted(store.decisions.values(), key=lambda d: d.id)
    if ship_id is not None:
        items = [d for d in items if d.ship_id == ship_id]
    if decision_maker is not None:
        items = [d for d in items if d.decision_maker == decision_maker]
    page = items[skip : skip + limit]
    return {
        "decisions": [_decision_out(d) for d in page],
        "total_count": len(items),
        "filters": {"ship_id": ship_id, "decision_maker": decision_maker},
        "skip": skip,
        "limit": limit,
    }


@router.post("/decisions", status_code=201)
async def create_decision(decision: DecisionCreate):
    """Log a new decision (AI recommendation or crew decision)"""
    async with store.lock:
        rec = Decision(
            id=store.next_decision_id(),
            ship_id=decision.ship_id,
            decision_type=decision.decision_type.value,
            decision_maker=decision.decision_maker.value,
            recommended_action=decision.recommended_action,
            reasoning=decision.reasoning,
            confidence_score=decision.confidence_score,
        )
        store.decisions[rec.id] = rec
    return {"decision": _decision_out(rec), "status": "logged"}


@router.get("/decisions/{decision_id}")
async def get_decision_details(decision_id: int):
    """Full details of a specific decision"""
    return {"decision": _decision_out(_decision_or_404(decision_id))}


@router.post("/decisions/{decision_id}/approve")
async def approve_decision(decision_id: int, approval: DecisionApproval):
    """Approve or reject a pending decision"""
    d = _decision_or_404(decision_id)
    if d.status != "pending_approval":
        raise HTTPException(status_code=409, detail=f"Decision {decision_id} is {d.status}, not pending approval")
    async with store.lock:
        d.status = "approved" if approval.approved else "rejected"
        d.approver_id = approval.approver_id
        d.approval_notes = approval.notes
        d.decided_at = datetime.now(timezone.utc)
    store.queue.enqueue({"event": "decision_" + d.status, "decision_id": d.id})
    return {"decision": _decision_out(d), "approved": approval.approved}


@router.post("/decisions/{decision_id}/execute")
async def execute_decision(decision_id: int):
    """Execute an approved decision (approval required first)"""
    d = _decision_or_404(decision_id)
    if d.status != "approved":
        raise HTTPException(status_code=409, detail=f"Decision {decision_id} is {d.status}; only approved decisions can be executed")
    async with store.lock:
        d.status = "executed"
        d.executed_at = datetime.now(timezone.utc)
    store.queue.enqueue({"event": "decision_executed", "decision_id": d.id})
    return {"decision": _decision_out(d), "executed": True}


@router.get("/decisions/{decision_id}/reasoning")
async def explain_decision(decision_id: int):
    """AI reasoning for a decision, from the logged record"""
    d = _decision_or_404(decision_id)
    return {
        "decision_id": d.id,
        "reasoning": d.reasoning,
        "confidence_score": d.confidence_score,
        "note": "reasoning as logged at creation; not recomputed",
    }

