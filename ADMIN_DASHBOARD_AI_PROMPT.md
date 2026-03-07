# 🛡️ ADMIN DASHBOARD — AI BUILD PROMPT

## Project Overview
Build a **React + Vite + Tailwind CSS** Admin Dashboard for the SCET Smart Parking System. This is the security/operations control center. Use **Lucide React** for icons. The dashboard connects to a **FastAPI backend** (http://localhost:8000) and **Firebase Realtime Database** for live updates.

## Tech Stack
- React 18+ with Vite
- Tailwind CSS (latest)
- Lucide React icons
- Firebase SDK (for real-time listeners)
- Fetch/Axios for REST API calls

## Design Requirements
- **Dark theme** with glassmorphism panels
- Sidebar navigation
- Modern, premium feel — gradients, subtle animations, hover effects
- Mobile responsive
- Color palette: Deep navy (#0f172a), Electric blue (#3b82f6), Emerald green (#10b981), Amber (#f59e0b), Red (#ef4444)

---

## Firebase Config (for real-time listeners)
```javascript
import { initializeApp } from "firebase/app";
import { getDatabase, ref, onValue } from "firebase/database";

const firebaseConfig = {
  apiKey: "AIzaSyC6i4-9iy_f3fd8jlnLFgvYY25iRi1JvCY",
  authDomain: "anpr-for.firebaseapp.com",
  databaseURL: "https://anpr-for-default-rtdb.firebaseio.com",
  projectId: "anpr-for",
  storageBucket: "anpr-for.firebasestorage.app",
  messagingSenderId: "593668402418",
  appId: "1:593668402418:web:46d87caa700e3622d2346b",
  measurementId: "G-YS2RF8M8FG"
};

const app = initializeApp(firebaseConfig);
const database = getDatabase(app);

// Real-time listener paths:
// /gate_events      — live operations feed
// /zones            — zone capacities
// /system_alerts    — exception center alerts
// /parking_sessions — active sessions
```

## API Base URL
```javascript
// DEFAULT (if dashboard and backend are running on the SAME PC):
const API_BASE_URL = "http://localhost:8000";

// IF BACKEND IS ON ANOTHER PC: Update to the server PC's local IP address.
// Find it by running `ipconfig` on the server PC → look for IPv4 Address.
// Example: const API_BASE_URL = "http://192.168.1.100:8000";
```

## Pages & Components

### 1. Login Page
Simple admin login. For MVP, use hardcoded credentials: `admin@scet.ac.in` / `admin123`.

### 2. Dashboard Layout (Shell)
- **Sidebar** (collapsible): Live Feed, Zones, Alerts, Analytics, Lookup, Visitors, Users, Settings
- **Top bar**: "SCET Smart Parking — Admin" + notification bell + logout
- **Content area**: renders the active page

### 3. Live Operations Feed (`/gate/events`)
Real-time table showing gate events. Use Firebase `onValue("/gate_events")` for instant updates. The feed must explicitly track where vehicles are moving.

| Column | Source | Notes |
|--------|--------|-------|
| Timestamp | `event.timestamp` | Format to readable time |
| Plate Number | `event.plate_number` | Large and bold |
| Gate Direction | `event.gate_type` | Explicitly display: **✅ Taking Entry** or **⬅️ Moving Out (Exit)** |
| Gate Location | `event.gate_id` | Name of the gate (e.g., "Main Gate", "Gate 1", "Revolving Gate") |
| Confidence | `event.confidence` | Show as % badge |
| Status | `event.resolved_status` | Color badges: 🟢 AUTHORIZED, 🟡 PENDING, 🔴 DENIED, 🟠 UNKNOWN, 🛡️ GUARDIAN_BLOCKED |
| Action | "Allow Entry" / "Deny Entry" | Buttons for manual override, especially for UNKNOWN/PENDING events |

**Action buttons at top:**
- "Manual Plate Entry" → opens manual entry modal
- "Complete Logs" → Opens full historical logs of all vehicle movements

### 4. Manual Plate Entry Modal
When OCR fails, admin types a plate number.
- **Input**: Plate number field
- **On typing**: Call `GET /admin/lookup/{plate}` — if found, auto-fill owner name, phone, vehicle type
- **If not found**: Show extra fields: Driver Name, Driver Phone, Notes
- **Submit**: `POST /gate/manual-entry`
- **Gate type selector**: Entry / Exit

### 5. Zone Management
Visual cards for each zone. Use Firebase `onValue("/zones")`.

Each zone card shows:
- Zone name + type icon (🏍️ bike, 🚗 car, 🔄 buffer)
- Progress bar: `current_count / capacity`
- Percentage utilization
- Color: Green (<60%), Yellow (60-80%), Red (>80%), Flashing red (100%)
- Buffer zone card should have a special "BUFFER" badge and show current designation

**API**: `GET /admin/zones`

### 6. Exception Center (Alerts)
Shows system alerts requiring admin action. Firebase `onValue("/system_alerts")`.

Each alert card:
- Type badge: UNKNOWN_PLATE (orange), GUARDIAN_BLOCK (red), BLACKLIST (dark red)
- Plate number
- Message
- Timestamp
- **Image thumbnail** if `image_url` exists (click to expand — especially important for Guardian alerts)
- "Resolve" button → `POST /admin/alerts/{alert_id}/resolve`

**Filter tabs**: All | Unresolved | Resolved

### 7. Analytics
Dashboard overview cards. API: `GET /admin/analytics`

Cards:
- 🚗 Entries Today: `today_entries`
- 🚶 Exits Today: `today_exits`
- 🅿️ Active Sessions: `active_sessions`
- 📊 Overall Utilization: `overall_utilization_pct`%
- 👥 Total Users: `total_users`
- ⚠️ Unresolved Alerts: `unresolved_alerts`

Bar chart: `hourly_distribution` (24h distribution)

### 8. Vehicle/User Lookup
Search bar for plate numbers.

- Input: Plate number
- API: `GET /admin/lookup/{plate_number}`
- If found, show: Owner name, phone, vehicle type, registration date, active session info
- If not found, show "Not registered" message

### 9. Visitor Management
List + registration form.

**List**: `GET /visitor/list`
Table: Visitor Name | Host | Plate | Expected Date | Status

**Register Form**: `POST /admin/register-visitor`
Fields: Host (dropdown of users from `GET /admin/users`), Visitor Name, Visitor Phone, Plate Number, Expected Date

### 10. Vehicle Registration (Admin Override)
Allow admins to register additional vehicles for users who have reached their 1-vehicle limit on the User Dashboard.
- Form: Select User (dropdown), Plate Number, Vehicle Type (2-wheeler/4-wheeler)
- API: `POST /user/vehicle` with `{plate_number, owner_id (from dropdown), vehicle_type}`

### 11. User Management
Table of all registered users. API: `GET /admin/users`
Columns: Name | Email | Phone | Role | Guardian Mode (🛡️ badge) | Default Zone | Registered

---

## API Reference

**Base URL**: Use the `API_BASE_URL` constant defined above (e.g., `http://192.168.X.X:8000`)

### Gate
| Method | Endpoint | Body | Notes |
|--------|----------|------|-------|
| POST | `/gate/trigger` | `{plate_number, gate_type, confidence, gate_id, image_url}` | ALPR trigger |
| POST | `/gate/manual-entry` | `{plate_number, gate_type, gate_id, driver_name?, driver_phone?, notes?}` | Manual entry. Returns `{plate_found, owner_info}` |
| POST | `/gate/resolve/{event_id}` | `{action: "allow"|"deny", notes?}` | Resolve event |
| GET | `/gate/events?limit=50` | — | List recent events |

### Admin
| Method | Endpoint | Body | Notes |
|--------|----------|------|-------|
| GET | `/admin/zones` | — | Returns `{zones: [...]}` |
| GET | `/admin/alerts?resolved=false` | — | Returns `{alerts: [...]}` |
| POST | `/admin/alerts/{id}/resolve` | — | Resolve alert |
| GET | `/admin/analytics` | — | Dashboard stats |
| GET | `/admin/lookup/{plate}` | — | Auto-lookup. Returns `{found, vehicle, owner, active_session}` |
| GET | `/admin/users` | — | All users |
| GET | `/admin/sessions?active_only=true` | — | Parking sessions |
| POST | `/admin/register-visitor` | `{host_id, visitor_name, visitor_phone?, plate_number?, expected_date?}` | Register visitor |

### Visitor
| Method | Endpoint | Body | Notes |
|--------|----------|------|-------|
| GET | `/visitor/list?host_id=X` | — | List visitors |
| DELETE | `/visitor/{id}` | — | Remove visitor |
