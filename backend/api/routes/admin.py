"""
Admin Routes — Zone management, alerts, analytics, vehicle lookup, visitor registration.
"""

import uuid
import time
from fastapi import APIRouter, HTTPException
from typing import Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from firebase_config import ref
from api.models import VisitorRegisterPayload

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════════
#  ZONES
# ═══════════════════════════════════════════════════════════════

@router.get("/zones")
def get_zones():
    """Live zone capacities — powers the dashboard zone management panel."""
    zones = ref("/zones").get() or {}
    result = []
    for zid, zdata in zones.items():
        zdata["zone_id"] = zid
        zdata["utilization_pct"] = round(
            (zdata.get("current_count", 0) / max(zdata.get("capacity", 1), 1)) * 100, 1
        )
        result.append(zdata)
    return {"zones": result}


@router.get("/zones/{zone_id}")
def get_zone(zone_id: str):
    """Get a single zone's details."""
    zone = ref(f"/zones/{zone_id}").get()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    zone["zone_id"] = zone_id
    return zone


# ═══════════════════════════════════════════════════════════════
#  SYSTEM ALERTS
# ═══════════════════════════════════════════════════════════════

@router.get("/alerts")
def get_alerts(resolved: Optional[bool] = False):
    """Get system alerts (UNKNOWN plates, Guardian blocks, etc.)."""
    alerts = ref("/system_alerts").get() or {}
    result = []
    for aid, adata in alerts.items():
        if resolved is None or adata.get("resolved", False) == resolved:
            adata["alert_id"] = aid
            result.append(adata)
    result.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return {"alerts": result, "count": len(result)}


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str):
    """Mark an alert as resolved."""
    alert = ref(f"/system_alerts/{alert_id}").get()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    ref(f"/system_alerts/{alert_id}").update({
        "resolved": True,
        "resolved_at": int(time.time() * 1000),
    })
    return {"status": "ok", "message": f"Alert {alert_id} resolved."}


# ═══════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════

@router.get("/analytics")
def get_analytics():
    """Aggregated parking analytics for the dashboard."""
    events = ref("/gate_events").get() or {}
    sessions = ref("/parking_sessions").get() or {}
    zones = ref("/zones").get() or {}
    users = ref("/users").get() or {}
    alerts = ref("/system_alerts").get() or {}

    now = int(time.time() * 1000)
    today_start = now - (now % 86400000)  # Midnight today (approx)

    # Today's entries
    today_entries = sum(
        1 for e in events.values()
        if e.get("timestamp", 0) >= today_start and e.get("gate_type") == "entry"
    )
    today_exits = sum(
        1 for e in events.values()
        if e.get("timestamp", 0) >= today_start and e.get("gate_type") == "exit"
    )

    # Active sessions
    active_count = sum(1 for s in sessions.values() if s.get("is_active"))

    # Total zone capacity & usage
    total_capacity = sum(z.get("capacity", 0) for z in zones.values())
    total_occupied = sum(z.get("current_count", 0) for z in zones.values())

    # Unresolved alerts
    unresolved_alerts = sum(1 for a in alerts.values() if not a.get("resolved"))

    # Hourly distribution (last 24h)
    hourly = {}
    for e in events.values():
        ts = e.get("timestamp", 0)
        if ts >= now - 86400000:
            hour = time.strftime("%H:00", time.localtime(ts / 1000))
            hourly[hour] = hourly.get(hour, 0) + 1

    return {
        "today_entries": today_entries,
        "today_exits": today_exits,
        "active_sessions": active_count,
        "total_capacity": total_capacity,
        "total_occupied": total_occupied,
        "overall_utilization_pct": round((total_occupied / max(total_capacity, 1)) * 100, 1),
        "total_users": len(users),
        "unresolved_alerts": unresolved_alerts,
        "hourly_distribution": dict(sorted(hourly.items())),
    }


# ═══════════════════════════════════════════════════════════════
#  VEHICLE / USER LOOKUP
# ═══════════════════════════════════════════════════════════════

@router.get("/lookup/{plate_number}")
def lookup_plate(plate_number: str):
    """
    Auto-lookup a plate number.
    Returns owner info if found, or empty if not.
    Used by admin manual-entry form for auto-fill.
    """
    plate = plate_number.upper().replace(" ", "")
    vehicle = ref(f"/vehicles/{plate}").get()

    if not vehicle:
        return {"found": False, "plate_number": plate, "message": "Vehicle not registered."}

    owner_id = vehicle.get("owner_id")
    owner = ref(f"/users/{owner_id}").get() if owner_id else None

    # Active session?
    sessions = ref("/parking_sessions").get() or {}
    active_session = None
    for sid, sess in sessions.items():
        if sess.get("plate_number") == plate and sess.get("is_active"):
            active_session = {"session_id": sid, **sess}
            break

    return {
        "found": True,
        "plate_number": plate,
        "vehicle": vehicle,
        "owner": {**owner, "user_id": owner_id} if owner else None,
        "active_session": active_session,
    }


@router.get("/users")
def list_users():
    """List all registered users (for admin panel)."""
    users = ref("/users").get() or {}
    result = []
    for uid, u in users.items():
        u["user_id"] = uid
        result.append(u)
    return {"users": result, "count": len(result)}


# ═══════════════════════════════════════════════════════════════
#  VISITOR REGISTRATION (Admin side)
# ═══════════════════════════════════════════════════════════════

@router.post("/register-visitor")
def admin_register_visitor(payload: VisitorRegisterPayload):
    """Admin registers an expected visitor."""
    visitor_id = str(uuid.uuid4())
    visitor_data = {
        "host_id": payload.host_id,
        "visitor_name": payload.visitor_name,
        "visitor_phone": payload.visitor_phone or "",
        "plate_number": payload.plate_number.upper().replace(" ", "") if payload.plate_number else "",
        "expected_date": payload.expected_date or "",
        "approved": True,  # Admin-approved by default
        "created_at": int(time.time() * 1000),
        "registered_by": "admin",
    }

    ref(f"/visitors/{visitor_id}").set(visitor_data)

    return {
        "status": "ok",
        "visitor_id": visitor_id,
        "message": f"Visitor {payload.visitor_name} registered.",
        "visitor": visitor_data,
    }


# ═══════════════════════════════════════════════════════════════
#  PARKING SESSIONS
# ═══════════════════════════════════════════════════════════════

@router.get("/sessions")
def list_sessions(active_only: bool = True):
    """List parking sessions."""
    sessions = ref("/parking_sessions").get() or {}
    result = []
    for sid, s in sessions.items():
        if active_only and not s.get("is_active"):
            continue
        s["session_id"] = sid
        result.append(s)
    result.sort(key=lambda x: x.get("entry_time", 0), reverse=True)
    return {"sessions": result, "count": len(result)}
