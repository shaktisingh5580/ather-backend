# 📱 USER DASHBOARD — PAGING FEATURE AI PROMPT

## Context
You are adding the **"Peer-to-Peer Paging"** feature to the React + Vite + Tailwind User Dashboard. This feature allows users to report an improperly parked or blocking vehicle via the dashboard.

## Feature Overview
1. **Goal**: Let users notify the owner of a blocking car directly by inputting their license plate.
2. **Backend API**: `POST /user/page-vehicle`
3. **Real-time Impact**: The backend will automatically send a WhatsApp/Telegram alert to the wrongdoer and log a `SystemAlert` to the Admin Dashboard's Exception Center.

## UI Requirements
Create a new section/card on the User Dashboard (e.g., inside the main dashboard view or a dedicated "Report Issue" page).

### Design Elements
- **Card Title**: "Report Blocking Vehicle" or "Page a Vehicle"
- **Icon**: Use a Lucide React icon like `AlertTriangle` or `Megaphone`
- **Input Field**: Large, clear input for the **Plate Number** (e.g., "GJ05TK9111")
- **Optional Input**: A short text area for a custom message (e.g., "Blocking my exit in Zone A")
- **Action Button**: A prominent "Send Alert" or "Page Owner" button. Use styling that implies action (e.g., amber or warning color). 

### Behavior and State Management
1. When the user submits the form:
   - Show a loading spinner on the button.
   - Make a `POST` request to `API_BASE_URL + "/user/page-vehicle"`.
   - **Request Body**:
     ```javascript
     {
       blocked_plate: "plate_number_from_input",
       reporter_id: "current_user_id", // From localStorage or auth state
       message: "optional_custom_message"
     }
     ```
2. **Success Handling**:
   - On `200 OK`, clear the inputs.
   - Display a success toast or inline message: *"The vehicle owner has been notified via WhatsApp, and campus security has been alerted."*
3. **Error Handling**:
   - On `404 Not Found`, display an error message: *"Vehicle not found in the system. Please verify the plate number."*
   - Manage the error state elegantly with red text or an error toast.

## Code Example Snippet to Integrate
```javascript
const handlePageVehicle = async (e) => {
  e.preventDefault();
  setIsLoading(true);
  setError(null);
  setSuccess(false);

  try {
    const response = await fetch(`${API_BASE_URL}/user/page-vehicle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        blocked_plate: plateNumber,
        reporter_id: currentUser.user_id,
        message: customMessage,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Failed to page vehicle");
    }

    setSuccess(true);
    setPlateNumber("");
    setCustomMessage("");
  } catch (err) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};
```
