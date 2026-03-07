# 👤 USER DASHBOARD — REGISTRATION PAGE PROMPT

## Context
You are modifying the React + Vite User Dashboard for the SCET Smart Parking System. Currently, the login flow attempts a `POST /user/login`. If it returns a 404, we need to show a robust registration form. Users need a dedicated route (e.g., `/register`) so that they can be linked to this page via a QR code at the security desk.

## UI Requirements

### 1. Dedicated Registration Route
- Create a specific route (e.g., `/register`) that renders the Registration component directly. 
- This page needs to be mobile-first and look like a slick app onboarding screen, since 99% of people will be viewing this on their phones after scanning the Admin's QR code.

### 2. Registration Form
Create a clean form with the following fields:
- **Full Name** (Input)
- **College Email** (Input, hint: must use `@scet.ac.in`)
- **Phone Number** (Input, tell user it will be used for WhatsApp alerts)
- **Role** (Select dropdown: `student` or `staff` — default to `student`)
- **Submit Button**: 
  - Makes a `POST` request to `${API_BASE_URL}/user/register` with the JSON body.
  - Show a loading spinner during the request.

### 3. Post-Registration Flow
1. Upon a successful `200 OK` response from `/user/register`:
   - Store the returned `user_id` in localStorage or your auth state provider.
   - Automatically redirect the user to the main Dashboard/Profile page (`/` or `/dashboard`).
2. Show a welcome toast: *"Welcome! Please add your vehicle to complete setup."*

## Integration Logic
```javascript
const handleRegister = async (e) => {
  e.preventDefault();
  setIsLoading(true);
  
  try {
    const response = await fetch(`${API_BASE_URL}/user/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: formData.name,
        email: formData.email,
        phone: formData.phone,
        role: formData.role
      })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Login successful!
      localStorage.setItem("user_id", data.user_id);
      toast.success("Registration complete!");
      // Redirect to dashboard
      window.location.href = "/dashboard";
    } else {
      toast.error(data.detail || data.message || "Registration failed");
    }
  } catch (err) {
    toast.error("Network error. Please try again.");
  } finally {
    setIsLoading(false);
  }
};
```
