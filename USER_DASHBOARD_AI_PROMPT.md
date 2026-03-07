# 👤 USER DASHBOARD — AI BUILD PROMPT

## Project Overview
Build a **React + Vite + Tailwind CSS** User Dashboard for the SCET Smart Parking System. This is the student/staff portal where users manage their parking profile, vehicles, and settings. Use **Lucide React** for icons. Connects to a **FastAPI backend** (running on a separate server PC) and **Firebase Realtime Database** for live updates.

## Tech Stack
- React 18+ with Vite
- Tailwind CSS (latest)
- Lucide React icons
- Firebase SDK (for real-time listeners)
- Fetch/Axios for REST API calls

## Design Requirements
- **Clean modern light theme** with dark mode toggle
- Bottom navigation on mobile, sidebar on desktop
- Premium, app-like feel — smooth transitions, micro-animations
- Color palette: White (#ffffff), Slate (#f8fafc), Primary blue (#2563eb), Success green (#16a34a), Warning amber (#d97706), Danger red (#dc2626)
- Font: Inter or system-ui

---

## Authentication Flow
1. User enters their **college student email** (e.g., `21ce001@scet.ac.in`)
2. System calls `POST /user/login` with the email
3. If found → redirects to dashboard with user profile loaded
4. If not found (404) → shows registration form

**Registration**: `POST /user/register`
Fields: Full Name, College Email, Phone Number (with +91 prefix), Role (student/staff — default student)

**After login, store `user_id` in localStorage for subsequent API calls.**

**Important**: The dashboard URL is sent to users via WhatsApp on entry. So the login page should be clean and fast.

## Firebase Config
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
// /zones            — live zone heatmap
// /parking_sessions — current user's active session
// /gate_events      — recent events for user's plates
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

### 1. Login / Register Page
- Email input with `@scet.ac.in` domain hint
- "Login" button → `POST /user/login`
- If 404 → show inline registration form (no page change)
- After successful login/register → redirect to Profile

### 2. Profile Page
- Show: Full Name, Email, Phone, Role badge, Member Since
- "Edit Profile" button (name, phone editable)
- **Guardian Mode Section**:
  - Large toggle switch with status text: "🛡️ Guardian Mode: ACTIVE" (green) or "OFF" (gray)
  - Explanation: "When active, your vehicle cannot exit without your approval via WhatsApp."
  - API: `POST /user/guardian` with `{user_id, enabled: true/false}`
- **Active Parking Session** (if any):
  - Zone name, entry time, duration counter (live), gate entered

### 3. Vehicle Management
- Show the user's primary registered vehicle (from login response `vehicles[]`)
- Card: Plate number (large), Vehicle type badge (🏍️/🚗), Registration date
- **Add Vehicle Form**: Plate Number input, Vehicle Type dropdown (2-wheeler/4-wheeler)
  - **IMPORTANT LIMITATION**: Users can only register ONE vehicle from this dashboard.
  - If they already have a vehicle registered, hide the Add form and show a message: "You have reached your vehicle limit. Please contact the Admin to register additional vehicles."
  - API: `POST /user/vehicle` with `{plate_number, owner_id, vehicle_type}`
- **Remove Vehicle**: Delete button with confirmation
  - API: `DELETE /user/vehicle/{plate_number}`

### 4. Guardian Mode (Dedicated Page)
- Large visual toggle with animation
- Current status display
- **How it works** explanation card:
  - "Enable Guardian Mode to protect your vehicle from unauthorized exits."
  - "If someone tries to exit with your vehicle, you'll receive a WhatsApp photo alert."
  - "You must disable Guardian Mode from this dashboard before exiting."
- Recent guardian events for this user's vehicles (if any — filter `/system_alerts` by plate)

### 5. Parking Status
- **Current Session** card (if active):
  - Zone assigned (name + color), Entry time, Live duration counter
  - "Your vehicle is parked in: **North Strip (Zone A)**"
- **If no active session**: "You are not currently parked on campus."

### 6. Live Zone Heatmap
Visual representation of campus zone occupancy. Firebase `onValue("/zones")`.

For each zone, show a colored block:
- **Green** (< 60% full), **Yellow** (60-80%), **Orange** (80-95%), **Red** (> 95%)
- Show: Zone name, current/capacity, percentage
- The layout should roughly represent the campus map (top strip, east strip, etc.)
- Buffer zone (Echo) should show its current designation (bike/car/buffer)

### 7. Report Blocked Car (Paging)
- Input: Plate number of the car blocking you
- "Report" button → `POST /user/page-vehicle` with `{blocked_plate, reporter_id: <user_id>}`
- Success message: "The vehicle owner has been notified via WhatsApp."
- Error if plate not found in system
- **Design:** Use a Lucide React icon like `AlertTriangle` or `Megaphone`. Show a loading spinner on the button. Ensure elegant error handling if a `404 Not Found` returns.

### 8. Dedicated Registration Route (`/register`)
- Create a specific route (e.g., `/register`) that renders the Registration component directly.
- This page needs to be mobile-first and look like a slick app onboarding screen, since 99% of people will be viewing this on their phones after scanning the Admin's QR code.
- **Fields:** Full Name, College Email (`@scet.ac.in`), Phone Number (tell user it will be used for WhatsApp alerts), Role (`student` or `staff`).
- **Post-Registration Flow:** Upon successful `200 OK` from `/user/register`, store the returned `user_id` and automatically redirect to the main Dashboard (`/dashboard`). Show a welcome toast: "Welcome! Please add your vehicle to complete setup."

### 9. Map Navigation Trigger (Active Session)
- When a user has an active parking session, they should see a "Get Directions" or "Navigate" button next to their Zone Name in the **Current Session** card.
- **Icon:** Use the `Map` or `Navigation` icon.
- **Logic:** Look up the assigned zone's `latitude` and `longitude` from your loaded Firebase `/zones` store.
- **Action:** Open Google Maps in a new tab: `https://www.google.com/maps/dir/?api=1&destination=LAT,LNG`.

---

## API Reference

**Base URL**: Use the `API_BASE_URL` constant defined above (e.g., `http://192.168.X.X:8000`)

### User
| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/user/register` | `{full_name, email, phone, role?, default_zone?}` | `{user_id, profile}` |
| POST | `/user/login` | `{email}` | `{user_id, profile, vehicles, active_session}` |
| GET | `/user/{user_id}` | — | `{profile, vehicles, active_session}` |
| POST | `/user/vehicle` | `{plate_number, owner_id, vehicle_type}` | `{plate_number, vehicle}` |
| DELETE | `/user/vehicle/{plate}` | — | `{status}` |
| POST | `/user/guardian` | `{user_id, enabled}` | `{guardian_mode, message}` |
| POST | `/user/page-vehicle` | `{blocked_plate, reporter_id?, message?}` | `{status, page_id}` |

### Visitor
| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/visitor/register` | `{host_id, visitor_name, visitor_phone?, plate_number?, expected_date?}` | `{visitor_id, visitor}` |
| GET | `/visitor/list?host_id=X` | — | `{visitors: [...]}` |
| DELETE | `/visitor/{id}` | — | `{status}` |

### Zones (for heatmap)
| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/admin/zones` | `{zones: [{zone_id, name, capacity, current_count, zone_type, is_buffer}]}` |
