"""
Gate Routes — Handles ALPR triggers, manual entry, and event resolution.
"""

import uuid
import time
from fastapi import APIRouter, HTTPException

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from firebase_config import ref
from api.models import GateEventPayload, ManualEntryPayload, ResolveEventPayload

router = APIRouter(prefix="/gate", tags=["Gate"])


@router.post("/trigger")
def trigger_gate_event(payload: GateEventPayload):
    """
    Receive an ALPR detection event (from camera or mock simulator).
    Writes to /gate_events in Firebase. The Cloud Brain daemon picks it up.
    """
    event_id = str(uuid.uuid4())
    event_data = {
        "plate_number": payload.plate_number.upper().replace(" ", ""),
        "gate_type": payload.gate_type.value,
        "confidence": payload.confidence,
        "timestamp": int(time.time() * 1000),
        "resolved_status": "PENDING",
        "gate_id": payload.gate_id,
        "image_url": payload.image_url or "",
    }

    ref(f"/gate_events/{event_id}").set(event_data)

    return {
        "status": "ok",
        "event_id": event_id,
        "message": f"Gate event for {payload.plate_number} pushed. Cloud Brain will process.",
        "data": event_data,
    }


@router.post("/manual-entry")
def manual_entry(payload: ManualEntryPayload):
    """
    Admin manually enters a plate when OCR fails.
    Auto-lookup: if plate exists in /vehicles, returns owner info.
    If not, creates a temporary session with admin-provided details.
    """
    plate = payload.plate_number.upper().replace(" ", "")

    # Try to auto-lookup
    vehicle = ref(f"/vehicles/{plate}").get()
    owner_info = None

    if vehicle:
        owner_id = vehicle.get("owner_id")
        if owner_id:
            owner_info = ref(f"/users/{owner_id}").get()
            if owner_info:
                owner_info["user_id"] = owner_id

    # Create the gate event regardless
    event_id = str(uuid.uuid4())
    event_data = {
        "plate_number": plate,
        "gate_type": payload.gate_type.value,
        "confidence": 1.0,  # Manual = 100% confidence
        "timestamp": int(time.time() * 1000),
        "resolved_status": "AUTHORIZED",  # Admin-approved
        "gate_id": payload.gate_id,
        "image_url": "",
        "manual_entry": True,
        "admin_notes": payload.notes or "",
    }

    # If no vehicle found, store the driver info from manual input
    if not vehicle and payload.driver_name:
        event_data["manual_driver_name"] = payload.driver_name
        event_data["manual_driver_phone"] = payload.driver_phone or ""

    ref(f"/gate_events/{event_id}").set(event_data)

    return {
        "status": "ok",
        "event_id": event_id,
        "plate_found": vehicle is not None,
        "owner_info": owner_info,
        "message": f"Manual entry for {plate} processed.",
    }


@router.post("/resolve/{event_id}")
def resolve_event(event_id: str, payload: ResolveEventPayload):
    """
    Admin resolves an UNKNOWN or GUARDIAN_BLOCKED event.
    """
    event = ref(f"/gate_events/{event_id}").get()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    new_status = "AUTHORIZED" if payload.action == "allow" else "DENIED"
    ref(f"/gate_events/{event_id}").update({
        "resolved_status": new_status,
        "resolved_notes": payload.notes or "",
        "resolved_at": int(time.time() * 1000),
    })

    # Also resolve any matching system alert
    alerts = ref("/system_alerts").get() or {}
    for alert_id, alert in alerts.items():
        if (alert.get("plate_number") == event.get("plate_number")
                and not alert.get("resolved")):
            ref(f"/system_alerts/{alert_id}").update({
                "resolved": True,
                "resolved_at": int(time.time() * 1000),
            })

    return {
        "status": "ok",
        "event_id": event_id,
        "new_status": new_status,
        "message": f"Event resolved as {new_status}.",
    }


@router.get("/events")
def list_events(limit: int = 50):
    """Get recent gate events (for admin live feed)."""
    events = ref("/gate_events").order_by_child("timestamp").limit_to_last(limit).get() or {}
    result = []
    for eid, data in events.items():
        data["event_id"] = eid
        result.append(data)
    result.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return {"events": result, "count": len(result)}
