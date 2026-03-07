# Admin Dashboard — Frontend API Integration Guide

This document outlines the API endpoints, data structures, and workflows required to build the Frontend Admin Dashboard for the Smart Parking System. You will manage Live Zones, System Alerts, Gate Events, and overall Analytics.

## Base URL
All requests should be prefixed with your backend's base URL (e.g., `http://localhost:8000`).

---

## 1. Top-Level Analytics

### Get Analytics Dashboard Data
**Endpoint:** `GET /admin/analytics`
**Purpose:** Populates the overarching statistics on the admin homepage.
**Returns:**
```json
{
  "today_entries": Int,
  "today_exits": Int,
  "active_sessions": Int,
  "total_capacity": Int,
  "total_occupied": Int,
  "overall_utilization_pct": Float,
  "total_users": Int,
  "unresolved_alerts": Int,
  "hourly_distribution": Object (key=Hour, value=Count)
}
```

---

## 2. Live Zone Management

### Get All Zones
**Endpoint:** `GET /admin/zones`
**Purpose:** Fetches live capacity and occupancy for all zones (e.g., zone_a, zone_b).
**Returns:** Array of objects containing `zone_id`, `capacity`, `current_count`, `utilization_pct`.

---

## 3. Live Gate Events (The Feed)

### List Recent Events
**Endpoint:** `GET /gate/events?limit=50`
**Purpose:** Displays the live feed of ALPR camera detections (entries and exits).
**Returns:** Array of events including `event_id`, `plate_number`, `gate_type`, `resolved_status` (PENDING, AUTHORIZED, UNKNOWN), `confidence`.

### Resolve Gate Event (Exception Handling)
**Endpoint:** `POST /gate/resolve/{event_id}`
**Purpose:** When the ALPR flags a plate as UNKNOWN or GUARDIAN_BLOCKED, the admin can manually hit "Allow" or "Deny".
**Payload:**
```json
{
  "action": "allow" | "deny",
  "notes": "String (optional)"
}
```

### Manual Plate Entry (Override)
**Endpoint:** `POST /gate/manual-entry`
**Purpose:** If a vehicle plate is completely unreadable, the admin types it manually. This triggers entry logic instantly.
**Payload:**
```json
{
  "gate_id": "String",
  "gate_type": "entry" | "exit",
  "plate_number": "String",
  "driver_name": "String (optional)",
  "driver_phone": "String (optional)",
  "notes": "String"
}
```

---

## 4. System Security Alerts

### Get System Alerts
**Endpoint:** `GET /admin/alerts?resolved=false`
**Purpose:** Fetches active security breaches (Guardian Mode violations, Paging requests, etc.).
**Returns:** Array of alerts.

### Resolve Alert
**Endpoint:** `POST /admin/alerts/{alert_id}/resolve`
**Purpose:** Silences/resolves a security alert after the admin has investigated.

---

## 5. Vehicle / User Lookup & Registration

### Lookup License Plate
**Endpoint:** `GET /admin/lookup/{plate_number}`
**Purpose:** Search for a license plate in the system. Returns the vehicle data, the owner's profile, and any `active_session` details if the car is currently parked.

### List All Users
**Endpoint:** `GET /admin/users`
**Purpose:** Displays the user management table.

### Register Expected Visitor
**Endpoint:** `POST /admin/register-visitor`
**Purpose:** Pre-approves a visitor's plate for a specific expected date.
**Payload:**
```json
{
  "host_id": "String",
  "visitor_name": "String",
  "visitor_phone": "String (optional)",
  "plate_number": "String (optional)",
  "expected_date": "YYYY-MM-DD"
}
```

---

## Summary of Data Flow for Frontend Engineers
1. **Live Refreshes:** You should ideally poll `/admin/analytics`, `/gate/events`, and `/admin/zones` every 5-10 seconds to create a "Live" feel, or set up WebSocket connections if you upgrade the backend later.
2. **Exception Loop:** A common admin loop is: See UNKNOWN tag in `/gate/events` -> Type plate in `/admin/lookup` -> Confirm it belongs to someone -> Call `/gate/resolve/{event_id}` with `"allow"`.
