"""
Zone Seeder — Seeds SCET campus parking zones into Firebase.
Run once to initialize the zone data:
    cd backend && python seed_zones.py
"""

from firebase_config import ref

SCET_ZONES = {
    "zone_a": {
        "name": "North Strip",
        "location": "Top strip (Gate 5 → Revolving Gate)",
        "capacity": 1200,
        "current_count": 0,
        "zone_type": "bike",
        "is_buffer": False,
        "original_type": "bike",
        "latitude": 21.1834,
        "longitude": 72.8225
    },
    "zone_b": {
        "name": "East Strip",
        "location": "Right-side parking (east boundary)",
        "capacity": 800,
        "current_count": 0,
        "zone_type": "bike",
        "is_buffer": False,
        "original_type": "bike",
        "latitude": 21.1831,
        "longitude": 72.8230
    },
    "zone_c": {
        "name": "West Parking",
        "location": "Left-side parking (T.P. Road)",
        "capacity": 400,
        "current_count": 0,
        "zone_type": "mixed",
        "is_buffer": False,
        "original_type": "mixed",
        "latitude": 21.1835,
        "longitude": 72.8215
    },
    "zone_d": {
        "name": "South Parking",
        "location": "Bottom area (Gate 2, Gate 3, Parking No.3 & No.4)",
        "capacity": 300,
        "current_count": 0,
        "zone_type": "mixed",
        "is_buffer": False,
        "original_type": "mixed",
        "latitude": 21.1825,
        "longitude": 72.8220
    },
    "zone_e": {
        "name": "Mid-Right (Buffer)",
        "location": "Small block mid-right side",
        "capacity": 300,
        "current_count": 0,
        "zone_type": "buffer",
        "is_buffer": True,
        "original_type": "buffer",
        "latitude": 21.1828,
        "longitude": 72.8228
    },
}


def seed_zones(force: bool = False):
    """Seed zone data into Firebase. Set force=True to overwrite existing data."""
    existing = ref("/zones").get()

    if existing and not force:
        print("⚠️  Zones already seeded. Use --force to overwrite.")
        print(f"   Existing zones: {list(existing.keys())}")
        return

    ref("/zones").set(SCET_ZONES)

    print("✅ SCET Campus zones seeded successfully!")
    print(f"   Total zones: {len(SCET_ZONES)}")
    total_capacity = sum(z["capacity"] for z in SCET_ZONES.values())
    print(f"   Total capacity: {total_capacity} spots")
    print()
    for zid, z in SCET_ZONES.items():
        emoji = "🏍️" if z["zone_type"] == "bike" else "🔄" if z["is_buffer"] else "🚗+🏍️"
        print(f"   {emoji} {zid}: {z['name']} ({z['zone_type']}) — {z['capacity']} spots")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    seed_zones(force)
