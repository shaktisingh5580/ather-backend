from firebase_config import ref

print("Flushing bad mock data...")
ref("/users").delete()
ref("/vehicles").delete()
ref("/gate_events").delete()
ref("/parking_sessions").delete()
ref("/system_alerts").delete()
print("Done! Database is clean.")
