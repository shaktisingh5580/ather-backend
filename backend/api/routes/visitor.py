"""
Visitor Routes — Pre-register visitors (by host users or admin).
"""

import uuid
import time
from fastapi import APIRouter, HTTPException

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from firebase_config import ref
from api.models import VisitorRegisterPayload

router = APIRouter(prefix="/visitor", tags=["Visitor"])


@router.post("/register")
def register_visitor(payload: VisitorRegisterPayload):
    """
    Pre-register a visitor. Can be called by:
    - A host user (from User Dashboard)
    - An admin (from Admin Dashboard — uses /admin/register-visitor instead)
    """
    # Verify host exists
    host = ref(f"/users/{payload.host_id}").get()
    if not host:
        raise HTTPException(status_code=404, detail="Host user not found")

    visitor_id = str(uuid.uuid4())
    visitor_data = {
        "host_id": payload.host_id,
        "host_name": host.get("full_name", ""),
        "visitor_name": payload.visitor_name,
        "visitor_phone": payload.visitor_phone or "",
        "plate_number": payload.plate_number.upper().replace(" ", "") if payload.plate_number else "",
        "expected_date": payload.expected_date or "",
        "approved": True,
        "created_at": int(time.time() * 1000),
        "registered_by": "user",
    }

    ref(f"/visitors/{visitor_id}").set(visitor_data)

    return {
        "status": "ok",
        "visitor_id": visitor_id,
        "message": f"Visitor {payload.visitor_name} pre-registered by {host.get('full_name')}.",
        "visitor": visitor_data,
    }


@router.get("/list")
def list_visitors(host_id: str = None):
    """
    List visitors. Optionally filter by host_id.
    """
    visitors = ref("/visitors").get() or {}
    result = []
    for vid, v in visitors.items():
        if host_id and v.get("host_id") != host_id:
            continue
        v["visitor_id"] = vid
        result.append(v)
    result.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"visitors": result, "count": len(result)}


@router.delete("/{visitor_id}")
def remove_visitor(visitor_id: str):
    """Remove a visitor registration."""
    existing = ref(f"/visitors/{visitor_id}").get()
    if not existing:
        raise HTTPException(status_code=404, detail="Visitor not found")

    ref(f"/visitors/{visitor_id}").delete()
    return {"status": "ok", "message": "Visitor removed."}
