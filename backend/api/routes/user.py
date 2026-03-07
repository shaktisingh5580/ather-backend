"""
User Routes — Registration, login, vehicles, guardian mode, paging.
Authentication is via college student email (e.g. 21ce001@scet.ac.in).
"""

import uuid
import time
from fastapi import APIRouter, HTTPException

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from firebase_config import ref
from api.models import (
    UserRegisterPayload, UserLoginPayload, UserUpdatePayload, VehicleRegistration,
    GuardianToggle, PageVehicleRequest
)

router = APIRouter(prefix="/user", tags=["User"])


@router.post("/register")
def register_user(payload: UserRegisterPayload):
    """Register a new user with their college email."""
    # Check if email already exists
    users = ref("/users").get() or {}
    for uid, u in users.items():
        if u.get("email") == payload.email:
            return {
                "status": "exists",
                "user_id": uid,
                "message": f"User with email {payload.email} already registered.",
                "profile": u,
            }

    user_id = str(uuid.uuid4())
    user_data = {
        "full_name": payload.full_name,
        "email": payload.email,
        "phone": payload.phone,
        "role": payload.role.value,
        "guardian_mode": False,
        "default_zone": payload.default_zone or "zone_a",
        "created_at": int(time.time() * 1000),
    }

    ref(f"/users/{user_id}").set(user_data)

    return {
        "status": "ok",
        "user_id": user_id,
        "message": f"User {payload.full_name} registered successfully.",
        "profile": user_data,
    }


@router.post("/login")
def login_user(payload: UserLoginPayload):
    """Login via college email. Returns user profile + vehicles."""
    users = ref("/users").get() or {}
    for uid, u in users.items():
        if u.get("email") == payload.email:
            # Fetch user's vehicles
            vehicles = ref("/vehicles").get() or {}
            user_vehicles = [
                {"plate_number": plate, **vdata}
                for plate, vdata in vehicles.items()
                if vdata.get("owner_id") == uid
            ]
            # Fetch active parking session
            sessions = ref("/parking_sessions").get() or {}
            active_session = None
            for sid, sess in sessions.items():
                if sess.get("user_id") == uid and sess.get("is_active"):
                    active_session = {"session_id": sid, **sess}
                    break

            u["user_id"] = uid
            return {
                "status": "ok",
                "user_id": uid,
                "profile": u,
                "vehicles": user_vehicles,
                "active_session": active_session,
            }

    raise HTTPException(status_code=404, detail="Email not found. Please register first.")


@router.get("/{user_id}")
def get_user(user_id: str):
    """Get a user's full profile, vehicles, and active session."""
    user = ref(f"/users/{user_id}").get()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user["user_id"] = user_id

    # Vehicles
    vehicles = ref("/vehicles").get() or {}
    user_vehicles = [
        {"plate_number": plate, **vdata}
        for plate, vdata in vehicles.items()
        if vdata.get("owner_id") == user_id
    ]

    # Active session
    sessions = ref("/parking_sessions").get() or {}
    active_session = None
    for sid, sess in sessions.items():
        if sess.get("user_id") == user_id and sess.get("is_active"):
            active_session = {"session_id": sid, **sess}
            break

    return {
        "profile": user,
        "vehicles": user_vehicles,
        "active_session": active_session,
    }


@router.put("/")
def update_user_profile(payload: UserUpdatePayload):
    """Update a user's profile."""
    user_ref = ref(f"/users/{payload.user_id}")
    user = user_ref.get()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = {}
    if payload.full_name is not None:
        update_data["full_name"] = payload.full_name
    if payload.phone is not None:
        update_data["phone"] = payload.phone
        
    if update_data:
        user_ref.update(update_data)

    return {
        "status": "ok", 
        "message": "Profile updated successfully.", 
        "updated_fields": update_data
    }


@router.post("/vehicle")
def register_vehicle(payload: VehicleRegistration):
    """Register a vehicle to a user."""
    # Verify user exists
    user = ref(f"/users/{payload.owner_id}").get()
    if not user:
        raise HTTPException(status_code=404, detail="Owner user not found")

    # Enforce 1-vehicle limit (unless admin_override is true)
    all_vehicles = ref("/vehicles").get() or {}
    user_vehicles_count = sum(1 for v in all_vehicles.values() if v.get("owner_id") == payload.owner_id)
    
    # We allow the payload to pass `admin_override`, assuming basic MVP trust
    is_admin = getattr(payload, "admin_override", False)
    
    if user_vehicles_count >= 1 and not is_admin:
        raise HTTPException(
            status_code=403, 
            detail="Vehicle limit reached. Users can only register 1 vehicle. Please contact Admin for additional vehicles."
        )

    plate = payload.plate_number.upper().replace(" ", "")

    # Check if plate already registered
    existing = ref(f"/vehicles/{plate}").get()
    if existing:
        return {
            "status": "exists",
            "message": f"Vehicle {plate} is already registered.",
            "vehicle": existing,
        }

    vehicle_data = {
        "owner_id": payload.owner_id,
        "vehicle_type": payload.vehicle_type.value,
        "registered_at": int(time.time() * 1000),
    }

    ref(f"/vehicles/{plate}").set(vehicle_data)

    return {
        "status": "ok",
        "plate_number": plate,
        "message": f"Vehicle {plate} registered to {user.get('full_name')}.",
        "vehicle": vehicle_data,
    }


@router.delete("/vehicle/{plate_number}")
def remove_vehicle(plate_number: str):
    """Remove a vehicle registration."""
    plate = plate_number.upper().replace(" ", "")
    existing = ref(f"/vehicles/{plate}").get()
    if not existing:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    ref(f"/vehicles/{plate}").delete()
    return {"status": "ok", "message": f"Vehicle {plate} removed."}


@router.post("/guardian")
def toggle_guardian(payload: GuardianToggle):
    """Toggle guardian mode for a user."""
    user = ref(f"/users/{payload.user_id}").get()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ref(f"/users/{payload.user_id}").update({"guardian_mode": payload.enabled})

    status_text = "ENABLED 🛡️" if payload.enabled else "DISABLED"
    return {
        "status": "ok",
        "guardian_mode": payload.enabled,
        "message": f"Guardian Mode {status_text} for {user.get('full_name')}.",
    }


@router.post("/page-vehicle")
def page_vehicle(payload: PageVehicleRequest):
    """
    Report a blocked car. Looks up owner and sends paging WhatsApp alert.
    """
    plate = payload.blocked_plate.upper().replace(" ", "")
    vehicle = ref(f"/vehicles/{plate}").get()

    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle {plate} not found in the system."
        )

    owner_id = vehicle.get("owner_id")
    owner = ref(f"/users/{owner_id}").get() if owner_id else None

    if not owner or not owner.get("phone"):
        raise HTTPException(
            status_code=404,
            detail="Vehicle owner has no phone number on file."
        )

    # Send paging alert via Telegram
    from telegram_service import send_paging_alert
    send_paging_alert(owner.get("phone"), plate)

    # Log the paging event for user records
    page_id = str(uuid.uuid4())
    ref(f"/paging_events/{page_id}").set({
        "blocked_plate": plate,
        "reporter_id": payload.reporter_id or "anonymous",
        "message": payload.message or "",
        "timestamp": int(time.time() * 1000),
        "owner_notified": True,
    })

    # Create a system alert so it appears on the Admin Exception Center
    alert_id = str(uuid.uuid4())
    reporter_name = "Anonymous"
    if payload.reporter_id:
        reporter = ref(f"/users/{payload.reporter_id}").get()
        if reporter:
            reporter_name = reporter.get("full_name", reporter_name)

    ref(f"/system_alerts/{alert_id}").set({
        "type": "PAGING",
        "plate_number": plate,
        "message": f"PAGING ALERT: {reporter_name} reported vehicle {plate} as blocking. {payload.message or ''}",
        "timestamp": int(time.time() * 1000),
        "resolved": False,
    })

    return {
        "status": "ok",
        "message": f"Paging alert sent to owner of {plate} and logged for Security admin.",
        "page_id": page_id,
        "alert_id": alert_id,
    }
