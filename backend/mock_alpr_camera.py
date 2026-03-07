"""
Mock ALPR Camera Simulator
Simulates the burst-capture voting algorithm output.
Pushes gate events with SCET demo plates to Firebase.

Run with:
    cd backend && python mock_alpr_camera.py
"""

import time
import uuid
from firebase_config import ref

# ── SCET Demo Plates ──
DEMO_PLATES = [
    "GJ05TK9111",
    "GJ05RD6677",
    "GJ05TY8899",
    "GJ05RE8686",
]

# Simulated gate camera image (placeholder)
MOCK_IMAGE_URL = "https://res.cloudinary.com/dolt93yno/image/upload/v1772825066/Screenshot_2026-03-07_005322_y6iiw4.png"


def push_event(plate: str, gate_type: str = "entry", gate_id: str = "gate_2", confidence: float = 0.95):
    """Push a simulated ALPR event to Firebase."""
    event_id = str(uuid.uuid4())
    event_data = {
        "plate_number": plate,
        "gate_type": gate_type,
        "confidence": confidence,
        "timestamp": int(time.time() * 1000),
        "resolved_status": "PENDING",
        "gate_id": gate_id,
        "image_url": MOCK_IMAGE_URL,
    }

    ref(f"/gate_events/{event_id}").set(event_data)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"  📸 [{ts}] Pushed: {plate} | {gate_type} | {gate_id} | conf={confidence} | id={event_id[:8]}...")
    return event_id


def interactive_mode():
    """Interactive CLI for testing."""
    print("=" * 60)
    print("  📷 SCET MOCK ALPR CAMERA SIMULATOR")
    print("  Simulates burst-capture voting algorithm")
    print("=" * 60)
    print(f"\n  Available demo plates:")
    for i, plate in enumerate(DEMO_PLATES, 1):
        print(f"    {i}. {plate}")
    print(f"    5. Custom plate")
    print(f"    6. Auto-sequence (all 4 plates enter)")
    print(f"    7. Exit simulation (all 4 plates exit)")
    print(f"    0. Quit")

    while True:
        print(f"\n{'─'*40}")
        choice = input("  Select plate [1-7, 0=quit]: ").strip()

        if choice == "0":
            print("  👋 Simulator stopped.")
            break

        if choice == "6":
            # Auto-sequence: all 4 plates enter
            print("\n  🚗 Auto-sequence: Simulating 4 vehicle entries...")
            for plate in DEMO_PLATES:
                push_event(plate, "entry", "gate_2")
                time.sleep(1)
            print("  ✅ All 4 vehicles entered!")
            continue

        if choice == "7":
            # All plates exit
            print("\n  🚗 Auto-sequence: Simulating 4 vehicle exits...")
            for plate in DEMO_PLATES:
                push_event(plate, "exit", "gate_1")
                time.sleep(1)
            print("  ✅ All 4 vehicles exited!")
            continue

        if choice == "5":
            plate = input("  Enter plate number: ").strip().upper().replace(" ", "")
            if not plate:
                print("  ⚠️ Empty plate, skipping.")
                continue
        elif choice in "1234":
            plate = DEMO_PLATES[int(choice) - 1]
        else:
            print("  ⚠️ Invalid choice.")
            continue

        # Gate type
        gt = input("  Gate type [e=entry, x=exit] (default=entry): ").strip().lower()
        gate_type = "exit" if gt in ("x", "exit") else "entry"

        # Gate ID
        gid = input("  Gate ID (default=gate_2): ").strip() or "gate_2"

        # Confidence (simulate burst-capture voting)
        print("  🔄 Simulating burst capture (4 frames)...")
        import random
        confidences = [round(random.uniform(0.75, 0.99), 2) for _ in range(4)]
        best_conf = max(confidences)
        print(f"    Frame confidences: {confidences}")
        print(f"    ✅ Voting result: best confidence = {best_conf}")

        push_event(plate, gate_type, gid, best_conf)


def batch_entry():
    """Quick batch: push all 4 demo plates as entries."""
    print("  🚗 Batch entry: pushing all demo plates...")
    for plate in DEMO_PLATES:
        push_event(plate, "entry", "gate_2")
        time.sleep(0.5)
    print("  ✅ Done!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        batch_entry()
    else:
        interactive_mode()
