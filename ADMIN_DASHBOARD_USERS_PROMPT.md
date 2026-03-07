# 🛡️ ADMIN DASHBOARD — USER MANAGEMENT & QR REGISTRATION PROMPT

## Context
You are adding the **"User Management"** page to the React + Vite Admin Dashboard for the SCET Smart Parking System. This page allows admins to view existing users, manually register new users, and generate a dynamic QR code for self-registration.

## Feature Overview
1. **Goal**: Allow admins to easily onboard new students and staff.
2. **Backend API**: The backend already has a fully working `POST /user/register` endpoint.
   - Endpoint: `${API_BASE_URL}/user/register`
   - Body: `{ full_name: "String", email: "String", phone: "String", role: "student" | "staff" }`

## UI Requirements

### 1. "Add User" Manual Form
Create a clean form card with the following fields:
- **Full Name** (Input)
- **College Email** (Input, e.g., `@scet.ac.in`)
- **Phone Number** (Input, with +91 prefix)
- **Role** (Select dropdown: `student`, `staff`, `guest`)
- **Submit Button**: Makes the `POST` request to `/user/register`.
  - On success (200 OK), show a success toast and clear the form.

### 2. "QR Code Self-Registration" Card
We want a way for students walking up to the security desk to just scan a code and register on their own phones!
- **Library Needed**: Install `qrcode.react` (i.e. `npm run install qrcode.react`)
- **Card UI**: A distinct card titled "Self-Registration QR".
- **QR Content**: The QR code should encode the absolute URL to the User Dashboard's registration page.
  - E.g., `https://ather-user-frontend.vercel.app/register`
- **Design**: Render the QR Code prominently in the center of the card. Add a "Copy Link" button beneath it in case the admin needs to text or email the link instead.

## Code Example Snippet for QR Code
```javascript
import { QRCodeSVG } from 'qrcode.react';

// Make sure this points to your ACTUAL deployed User Dashboard URL
const REGISTRATION_URL = "https://ather-user-frontend.vercel.app/register";

export default function QRCodeCard() {
  return (
    <div className="p-6 bg-slate-800 rounded-xl flex flex-col items-center">
      <h3 className="text-white text-lg mb-4">Scan to Register</h3>
      <div className="p-4 bg-white rounded-lg">
        <QRCodeSVG value={REGISTRATION_URL} size={200} />
      </div>
      <p className="text-slate-400 mt-4 text-sm">
        Point your phone camera here to open the registration portal.
      </p>
    </div>
  );
}
```
