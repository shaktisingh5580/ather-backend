# 🗺️ USER DASHBOARD — MAP NAVIGATION TRIGGER

## Context
You are modifying the **"Active Parking Session"** card on the React + Vite User Dashboard to add Map Navigation functionality. 

## Feature Overview
1. When the user successfully enters the parking and is assigned a zone, the `GET /user/{user_id}` API responds with an `active_session` object.
2. The `active_session` object contains the `zone_parked` field (e.g., `"zone_a"`).
3. We need a way to let the user click a "Navigate to Zone" button that instantly opens Google Maps with directions to their assigned parking area.

## UI Requirements
Update the **Active Parking Session** component.

### Design Elements
- **Navigation Button**: Add a primary or secondary button next to the Zone Name.
- **Icon**: Use the `Map` or `Navigation` icon from Lucide React.
- **Label**: "Get Directions" or "Navigate"

### Data Flow & Logic
Since the backend `/admin/zones` endpoint (or the Firebase listener for `/zones`) returns the full zone objects, you need to extract the `latitude` and `longitude` fields for the zone the user is parked in.

```javascript
// Example helper function to generate the map link
const getGoogleMapsLink = (zoneId, allZonesData) => {
  const zone = allZonesData[zoneId];
  if (zone && zone.latitude && zone.longitude) {
    return `https://www.google.com/maps/dir/?api=1&destination=${zone.latitude},${zone.longitude}`;
  }
  return null; // Fallback if coords don't exist
};
```

### Implementation Steps
1. In the `ActiveSessionCard` component, find the user's current zone ID.
2. Look up the `latitude` and `longitude` from your loaded Firebase `/zones` store.
3. Render the `<a href={...} target="_blank" rel="noopener noreferrer">` tag wrapping the "Navigate" button using the Google Maps deep-link format `https://www.google.com/maps/dir/?api=1&destination=LAT,LNG`.
