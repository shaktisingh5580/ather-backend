"""
Test Scenarios & Real Profile Seeder
Injects real-looking student/staff profiles into Firebase and simulates their entries
to test WhatsApp dispatch, Zone Allocation, and Guardian Mode.

Run with:
    cd backend && python test_scenarios.py
"""

import time
import uuid
import sys
from firebase_config import ref


# ── Step 1: Real-looking Users & Vehicles ──
USERS = [
    {
        "full_name": "Aarav Sharma",
        "email": "21ce001@scet.ac.in",
        "phone": "1732122734", # Testing real Telegram notification
        "role": "student",
        "guardian_mode": False,
        "default_zone": "zone_a",
        "plate": "UP16CV0939",
        "vehicle_type": "2-wheeler"
    },
    {
        "full_name": "Diya Patel",
        "email": "22it045@scet.ac.in",
        "phone": "1626712374", # Testing real Telegram Guardian Mode alert
        "role": "student",
        "guardian_mode": True,  # Guardian is ON for testing anti-theft
        "default_zone": "zone_b",
        "plate": "GJ01RS1837",
        "vehicle_type": "2-wheeler"
    },
    {
        "full_name": "Dr. Rohit Desai",
        "email": "rohit.desai@scet.ac.in",
        "phone": "+919824109111",
        "role": "staff",
        "guardian_mode": False,
        "default_zone": "zone_c",
        "plate": "GJ05TY8899",
        "vehicle_type": "4-wheeler"
    },
    {
        "full_name": "Priya Singh",
        "email": "20co112@scet.ac.in",
        "phone": "+919824109111",
        "role": "student",
        "guardian_mode": False,
        "default_zone": "zone_a",
        "plate": "GJ05RE8686",
        "vehicle_type": "2-wheeler"
    }
]


def seed_real_profiles():
    """Seeds the 4 real-looking users and their vehicles."""
    print("=" * 50)
    print(" 🧑‍🎓 SCET SMART PARKING — REAL PROFILE SEEDER")
    print("=" * 50)
    
    # Check if they exist to avoid duplicates
    existing_users = ref("/users").get() or {}
    seeded_count = 0
    
    for u in USERS:
        # Check by email
        exists = any(eu.get("email") == u["email"] for eu in existing_users.values())
        if exists:
            print(f"  ⏭️ User {u['email']} already exists. Skipping.")
            continue
            
        user_id = str(uuid.uuid4())
        ref(f"/users/{user_id}").set({
            "full_name": u["full_name"],
            "email": u["email"],
            "phone": u["phone"],
            "role": u["role"],
            "guardian_mode": u["guardian_mode"],
            "default_zone": u["default_zone"],
            "created_at": int(time.time() * 1000),
        })
        
        ref(f"/vehicles/{u['plate']}").set({
            "owner_id": user_id,
            "vehicle_type": u["vehicle_type"],
            "registered_at": int(time.time() * 1000),
        })
        print(f"  ✅ Added {u['full_name']} ({u['role']}) -> {u['plate']} ({u['vehicle_type']})")
        seeded_count += 1
        
    print(f"\n  🎉 Seeded {seeded_count} new profiles & vehicles.")


# ── Step 2: Simulate Entries for Testing ──

def push_event(plate: str, gate_type: str = "entry", gate_id: str = "gate_main"):
    """Pushes an ALPR event to test Cloud Brain logic."""
    event_id = str(uuid.uuid4())
    ref(f"/gate_events/{event_id}").set({
        "plate_number": plate,
        "gate_type": gate_type,
        "confidence": 0.98,
        "timestamp": int(time.time() * 1000),
        "resolved_status": "PENDING",
        "gate_id": gate_id,
        "image_url": "https://res.cloudinary.com/dolt93yno/image/upload/v1772825066/Screenshot_2026-03-07_005322_y6iiw4.png",
    })
    print(f"  📸 Mock Camera: Pushed {gate_type.upper()} for {plate} at {gate_id}")


def test_zone_allocation():
    """Simulates 4 entries to test the Zone Allocation & WhatsApp."""
    print("\n" + "=" * 50)
    print(" 🚗 TESTING ZONE ALLOCATION & WHATSAPP")
    print("    (Ensure `cloud_brain.py` is running!)")
    print("=" * 50)
    
    # Aarav (Bike) -> Should go to a bike zone (Zone A/B)
    push_event("GJ05TK9111", "entry", "gate_2")
    time.sleep(1.5)
    
    # Dr. Desai (Car) -> Should go to a mixed zone (Zone C/D)
    push_event("GJ05TY8899", "entry", "gate_main")
    time.sleep(1.5)
    
    # Priya (Bike) -> Should go to a bike zone
    push_event("GJ05RE8686", "entry", "gate_5")
    time.sleep(1.5)
    
    # Diya (Bike) -> Guardian Mode is ON. Entry is fine, but Exit will trigger alert.
    push_event("GJ01RS1837", "entry", "gate_revolving")
    
    print("\n  ✅ Check your `cloud_brain.py` logs to see the allocations!")
    print("  📱 If WhatsApp is configured, check your phone for Entry Notifications.")


def test_guardian_mode_exit():
    """Simulates a Guardian Mode restricted exit."""
    print("\n" + "=" * 50)
    print(" 🛡️ TESTING GUARDIAN MODE EXIT (Anti-theft)")
    print("=" * 50)
    
    # Diya has Guardian Mode ON. Her exit should be DENIED and alert sent.
    push_event("GJ05RD6677", "exit", "gate_1")
    
    print("\n  ✅ Check your `cloud_brain.py` logs to see the Guardian Block!")
    print("  📱 If WhatsApp + Cloudinary is configured, check your phone for the Photo Alert.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--seed":
        seed_real_profiles()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_zone_allocation()
        time.sleep(3)
        test_guardian_mode_exit()
    else:
        print("Usage:")
        print("   python test_scenarios.py --seed   (Seeds real profiles into Firebase)")
        print("   python test_scenarios.py --test   (Simulates entries/exits for testing)")
