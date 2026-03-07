"""
Cloud Brain — The Decision Engine Daemon
Listens to Firebase /gate_events in real-time.
Processes entries/exits, guardian mode, smart slot re-allocation, and WhatsApp dispatch.

Run with:
    cd backend && python cloud_brain.py
"""

import time
import uuid
import threading
from firebase_config import ref
from telegram_service import (
    send_entry_notification,
    send_guardian_alert,
    send_exit_notification,
    send_visitor_arrival,
)
from cloudinary_service import upload_gate_image, get_placeholder_image_url


# ═══════════════════════════════════════════════════════════════
#  ZONE LOGIC — Smart Slot Re-allocation
# ═══════════════════════════════════════════════════════════════

def find_best_zone(vehicle_type: str) -> dict:
    """
    Find the best zone for a vehicle.
    If primary zones are full, auto-flip the buffer zone.
    Returns zone info dict with zone_id.
    """
    zones = ref("/zones").get() or {}

    # Determine what zone types this vehicle can use
    if vehicle_type == "2-wheeler":
        preferred_types = ["bike", "mixed"]
    else:
        preferred_types = ["car", "mixed"]

    # First pass: find a non-buffer zone with capacity
    for zid, z in zones.items():
        if z.get("is_buffer"):
            continue
        if z.get("zone_type") in preferred_types:
            if z.get("current_count", 0) < z.get("capacity", 0):
                return {**z, "zone_id": zid}

    # Second pass: all preferred zones full → flip the buffer zone
    buffer_zone_id = None
    for zid, z in zones.items():
        if z.get("is_buffer"):
            buffer_zone_id = zid
            break

    if buffer_zone_id:
        buffer = zones[buffer_zone_id]
        new_type = "bike" if vehicle_type == "2-wheeler" else "car"

        # Flip the buffer zone type
        ref(f"/zones/{buffer_zone_id}").update({"zone_type": new_type})
        print(f"  🔄 SMART SLOT: Buffer zone {buffer_zone_id} re-designated to '{new_type}'")

        if buffer.get("current_count", 0) < buffer.get("capacity", 0):
            buffer["zone_type"] = new_type
            return {**buffer, "zone_id": buffer_zone_id}

    # Everything is full
    return None


# ═══════════════════════════════════════════════════════════════
#  CORE EVENT HANDLER
# ═══════════════════════════════════════════════════════════════

def handle_gate_event(event_id: str, event_data: dict):
    """
    Process a single gate event.
    This is the BRAIN — the central decision maker.
    """
    plate = event_data.get("plate_number", "")
    gate_type = event_data.get("gate_type", "entry")
    gate_id = event_data.get("gate_id", "gate_main")
    image_url = event_data.get("image_url", "")
    status = event_data.get("resolved_status", "PENDING")

    # Skip already processed events
    if status != "PENDING":
        return

    print(f"\n{'='*60}")
    print(f"  🧠 CLOUD BRAIN processing: {plate} | {gate_type} | {gate_id}")
    print(f"{'='*60}")

    # ── Step 1: Look up vehicle ──
    vehicle = ref(f"/vehicles/{plate}").get()

    if not vehicle:
        # Check if it's a pre-registered visitor
        visitors = ref("/visitors").get() or {}
        visitor_match = None
        for vid, v in visitors.items():
            if v.get("plate_number") == plate and v.get("approved"):
                visitor_match = v
                break

        if visitor_match:
            print(f"  👋 Visitor detected: {visitor_match.get('visitor_name')}")
            ref(f"/gate_events/{event_id}").update({"resolved_status": "AUTHORIZED"})

            # Notify host
            host = ref(f"/users/{visitor_match.get('host_id')}").get()
            if host and host.get("phone"):
                send_visitor_arrival(
                    host["phone"],
                    visitor_match.get("visitor_name", "Visitor"),
                    plate,
                    gate_id,
                )

            # Create session for visitor
            _create_session(event_id, None, plate, "zone_d", gate_type)
            return

        # UNKNOWN PLATE
        print(f"  ❌ UNKNOWN plate: {plate}")
        ref(f"/gate_events/{event_id}").update({"resolved_status": "UNKNOWN"})

        alert_id = str(uuid.uuid4())
        ref(f"/system_alerts/{alert_id}").set({
            "type": "UNKNOWN_PLATE",
            "plate_number": plate,
            "message": f"Unrecognized vehicle {plate} at {gate_id}. Manual action required.",
            "timestamp": int(time.time() * 1000),
            "resolved": False,
            "image_url": image_url,
            "gate_id": gate_id,
        })
        print(f"  🚨 System alert created: {alert_id}")
        return

    # ── Step 2: Get owner ──
    owner_id = vehicle.get("owner_id")
    owner = ref(f"/users/{owner_id}").get() if owner_id else None

    if not owner:
        print(f"  ⚠️ Vehicle {plate} has no valid owner.")
        ref(f"/gate_events/{event_id}").update({"resolved_status": "UNKNOWN"})
        return

    print(f"  👤 Owner: {owner.get('full_name')} | Phone: {owner.get('phone')}")

    # ── Step 3: Handle EXIT ──
    if gate_type == "exit":
        # Check Guardian Mode
        if owner.get("guardian_mode"):
            print(f"  🛡️ GUARDIAN MODE ACTIVE — EXIT BLOCKED!")

            # Upload image to Cloudinary
            cloud_image_url = image_url
            if image_url:
                try:
                    cloud_image_url = upload_gate_image(image_url, plate, gate_id)
                    print(f"  📸 Image uploaded to Cloudinary: {cloud_image_url}")
                except Exception as e:
                    print(f"  ⚠️ Cloudinary upload failed: {e}")
                    cloud_image_url = image_url  # Fall back to original URL
            else:
                cloud_image_url = get_placeholder_image_url()

            ref(f"/gate_events/{event_id}").update({"resolved_status": "GUARDIAN_BLOCKED"})

            # Create system alert WITH image
            alert_id = str(uuid.uuid4())
            ref(f"/system_alerts/{alert_id}").set({
                "type": "GUARDIAN_BLOCK",
                "plate_number": plate,
                "message": f"Guardian Mode exit block for {plate} by {owner.get('full_name')} at {gate_id}.",
                "timestamp": int(time.time() * 1000),
                "resolved": False,
                "image_url": cloud_image_url,
                "gate_id": gate_id,
            })

            # Send WhatsApp with photo
            if owner.get("phone"):
                send_guardian_alert(owner["phone"], plate, gate_id, cloud_image_url)

            print(f"  🚨 Guardian alert sent to {owner.get('phone')}")
            return

        # Normal exit — close parking session
        _close_session(plate)
        ref(f"/gate_events/{event_id}").update({"resolved_status": "AUTHORIZED"})

        # Calculate duration for exit notification
        sessions = ref("/parking_sessions").get() or {}
        for sid, sess in sessions.items():
            if sess.get("plate_number") == plate and not sess.get("is_active"):
                entry_time = sess.get("entry_time", 0)
                exit_time = sess.get("exit_time", int(time.time() * 1000))
                duration_mins = int((exit_time - entry_time) / 60000)
                hours, mins = divmod(duration_mins, 60)
                duration_str = f"{hours}h {mins}m" if hours else f"{mins} min"

                if owner.get("phone"):
                    send_exit_notification(owner["phone"], plate, duration_str)
                break

        print(f"  ✅ Exit authorized for {plate}")
        return

    # ── Step 4: Handle ENTRY — find zone, create session ──
    vehicle_type = vehicle.get("vehicle_type", "2-wheeler")
    zone = find_best_zone(vehicle_type)

    if not zone:
        print(f"  🚫 ALL ZONES FULL! Cannot assign {plate}.")
        ref(f"/gate_events/{event_id}").update({"resolved_status": "DENIED"})

        alert_id = str(uuid.uuid4())
        ref(f"/system_alerts/{alert_id}").set({
            "type": "CAPACITY_FULL",
            "plate_number": plate,
            "message": f"All zones full. Vehicle {plate} denied entry.",
            "timestamp": int(time.time() * 1000),
            "resolved": False,
        })
        return

    zone_id = zone.get("zone_id")
    zone_name = zone.get("name", zone_id)

    # Authorize entry
    ref(f"/gate_events/{event_id}").update({"resolved_status": "AUTHORIZED"})

    # Increment zone count
    current = zone.get("current_count", 0)
    ref(f"/zones/{zone_id}").update({"current_count": current + 1})

    # Create parking session
    _create_session(event_id, owner_id, plate, zone_id, gate_type)

    # Send WhatsApp/Telegram entry notification with Maps URL
    if owner.get("phone"):
        nav_link = None
        lat = zone.get("latitude")
        lng = zone.get("longitude")
        if lat and lng:
            nav_link = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
            
        send_entry_notification(owner["phone"], plate, zone_name, gate_id, nav_link=nav_link)

    print(f"  ✅ ENTRY AUTHORIZED → {plate} → Zone {zone_name} (slot {current + 1}/{zone.get('capacity')})")


# ═══════════════════════════════════════════════════════════════
#  SESSION HELPERS
# ═══════════════════════════════════════════════════════════════

def _create_session(event_id: str, user_id: str, plate: str, zone_id: str, gate_type: str):
    """Create a new parking session."""
    if gate_type != "entry":
        return
    session_id = str(uuid.uuid4())
    ref(f"/parking_sessions/{session_id}").set({
        "user_id": user_id or "visitor",
        "plate_number": plate,
        "zone_parked": zone_id,
        "entry_time": int(time.time() * 1000),
        "exit_time": None,
        "is_active": True,
        "gate_event_id": event_id,
    })
    print(f"  📝 Session created: {session_id}")


def _close_session(plate: str):
    """Close active parking session for a plate and decrement zone count."""
    sessions = ref("/parking_sessions").get() or {}
    for sid, sess in sessions.items():
        if sess.get("plate_number") == plate and sess.get("is_active"):
            exit_time = int(time.time() * 1000)
            ref(f"/parking_sessions/{sid}").update({
                "is_active": False,
                "exit_time": exit_time,
            })

            # Decrement zone count
            zone_id = sess.get("zone_parked")
            if zone_id:
                zone = ref(f"/zones/{zone_id}").get()
                if zone:
                    count = max(0, zone.get("current_count", 1) - 1)
                    ref(f"/zones/{zone_id}").update({"current_count": count})
                    print(f"  📉 Zone {zone_id} count → {count}")

            print(f"  📝 Session {sid} closed.")
            return


# ═══════════════════════════════════════════════════════════════
#  FIREBASE LISTENER
# ═══════════════════════════════════════════════════════════════

_processed_events = set()


def on_gate_event(event):
    """Firebase child_added listener callback."""
    if event.event_type == "put" and event.data:
        data = event.data
        path = event.path
        
        def process_event(key, value):
            if isinstance(value, dict) and key not in _processed_events:
                if value.get("resolved_status") == "PENDING":
                    _processed_events.add(key)
                    print(f"\n📡 New event detected: {key}")
                    try:
                        handle_gate_event(key, value)
                    except Exception as e:
                        import traceback
                        print(f"  ❌ Error processing {key}: {e}")
                        traceback.print_exc()

        if path == "/" or path == "":
            if isinstance(data, dict):
                for key, value in data.items():
                    process_event(key, value)
        else:
            key = path.strip("/")
            process_event(key, data)


def start_listener():
    """Start the Firebase real-time listener."""
    print("=" * 60)
    print("  🧠 SCET SMART PARKING — CLOUD BRAIN")
    print("  Listening for gate events on Firebase...")
    print("=" * 60)

    # Process any existing pending events first
    existing = ref("/gate_events").get() or {}
    for eid, edata in existing.items():
        if isinstance(edata, dict) and edata.get("resolved_status") == "PENDING":
            print(f"\n📡 Processing existing pending event: {eid}")
            _processed_events.add(eid)
            try:
                handle_gate_event(eid, edata)
            except Exception as e:
                print(f"  ❌ Error: {e}")

    # Start real-time listener
    ref("/gate_events").listen(on_gate_event)


if __name__ == "__main__":
    start_listener()

    # Keep the daemon alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Cloud Brain stopped.")
