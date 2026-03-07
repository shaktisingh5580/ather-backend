from firebase_config import ref

events = ref("/gate_events").get()
print(f"Total events in DB: {len(events) if events else 0}")
if events:
    pending = [e for e in events.values() if e.get("resolved_status") == "PENDING"]
    print(f"Pending events: {len(pending)}")
    for p in pending:
        print(p)

alerts = ref("/system_alerts").get()
print(f"\nTotal system alerts in DB: {len(alerts) if alerts else 0}")
if alerts:
    for a in alerts.values():
        print(a)
        
print("\nDone")
