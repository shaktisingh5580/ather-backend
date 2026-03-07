# User Dashboard — Frontend API Integration Guide

This document outlines the API endpoints, data structures, and workflows required to build the Frontend User Dashboard for the Smart Parking System.

## Base URL
All requests should be prefixed with your backend's base URL (e.g., `http://localhost:8000`).

---

## 1. Authentication & Profiling (Email-based)

### Register User
**Endpoint:** `POST /user/register`
**Purpose:** Registers a new user (student/staff).
**Payload:**
```json
{
  "full_name": "String",
  "email": "String (e.g., 21ce001@scet.ac.in)",
  "phone": "String",
  "role": "String (student, staff, guest)",
  "default_zone": "String (optional)"
}
```
**Response:** `user_id`, `profile`

### Login User
**Endpoint:** `POST /user/login`
**Purpose:** Logs a user in based on their email. Returns full context (vehicles, active parking session).
**Payload:**
```json
{
  "email": "String"
}
```
**Response:** `user_id`, `profile`, `vehicles` (Array), `active_session` (Object or null)

### Get User Profile
**Endpoint:** `GET /user/{user_id}`
**Purpose:** Fetches fresh data to populate the dashboard on reload.
**Response:** `profile`, `vehicles`, `active_session`

### Update Profile
**Endpoint:** `PUT /user/`
**Purpose:** Updates name or phone number.
**Payload:**
```json
{
  "user_id": "String",
  "full_name": "String (optional)",
  "phone": "String (optional)"
}
```

---

## 2. Vehicle Management

### Register a Vehicle
**Endpoint:** `POST /user/vehicle`
**Purpose:** Adds a vehicle to the user's account. **Note: Users are limited to 1 vehicle.**
**Payload:**
```json
{
  "owner_id": "String",
  "plate_number": "String (e.g., GJ05AB1234)",
  "vehicle_type": "car|motorcycle"
}
```

### Remove a Vehicle
**Endpoint:** `DELETE /user/vehicle/{plate_number}`
**Purpose:** Removes a registered vehicle.

---

## 3. Security & Guardian Mode

### Toggle Guardian Mode 🛡️
**Endpoint:** `POST /user/guardian`
**Purpose:** Locks/unlocks the user's vehicles. When verified entries/exits occur while locked, it triggers security alerts.
**Payload:**
```json
{
  "user_id": "String",
  "enabled": Boolean
}
```
**Response:** Updates `guardian_mode` state.

---

## 4. Paging (Reporting Blocked Vehicles)

### Page a Vehicle
**Endpoint:** `POST /user/page-vehicle`
**Purpose:** Used when a user is blocked by another car. Sends a WhatsApp/Telegram alert to the blocking car's owner.
**Payload:**
```json
{
  "reporter_id": "String (optional)",
  "blocked_plate": "String",
  "message": "String (optional)"
}
```
**Response:** Triggers WhatsApp/Telegram alert and creates an Admin System Alert.

---

## Summary of Data Flow for Frontend Engineers
1. **Initial Load:** Start at a Login/Registration screen. On successful auth, store the `user_id` in `localStorage`.
2. **Dashboard Overview:** Call `GET /user/{user_id}` on mount to get the `active_session` (if parked, show current zone and entry time), and list `vehicles`.
3. **State Updates:** If the user toggles Guardian Mode, call the `/user/guardian` endpoint and update UI state optimisticially.
