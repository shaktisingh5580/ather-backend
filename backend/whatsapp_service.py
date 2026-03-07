"""
WhatsApp Notification Service
Supports Twilio WhatsApp Sandbox (demo) and Meta Cloud API (production).
Sends entry notifications, guardian alerts with images, paging alerts, and visitor arrivals.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Twilio config ──
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# ── Meta Cloud API config ──
META_TOKEN = os.getenv("META_WHATSAPP_TOKEN")
META_PHONE_ID = os.getenv("META_PHONE_NUMBER_ID")

# ── App URLs ──
USER_DASHBOARD = os.getenv("USER_DASHBOARD_URL", "http://localhost:5174")
ADMIN_DASHBOARD = os.getenv("ADMIN_DASHBOARD_URL", "http://localhost:5173")


def _use_twilio() -> bool:
    """Check if Twilio credentials are configured."""
    return bool(TWILIO_SID and TWILIO_TOKEN)


def _use_meta() -> bool:
    """Check if Meta Cloud API credentials are configured."""
    return bool(META_TOKEN and META_PHONE_ID)


# ═══════════════════════════════════════════════════════════════
#  TWILIO SENDER
# ═══════════════════════════════════════════════════════════════

def _send_twilio(to_phone: str, body: str, media_url: str = None):
    """Send a WhatsApp message via Twilio."""
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        params = {
            "from_": TWILIO_FROM,
            "to": f"whatsapp:{to_phone}" if not to_phone.startswith("whatsapp:") else to_phone,
            "body": body,
        }
        if media_url:
            params["media_url"] = [media_url]

        message = client.messages.create(**params)
        print(f"  📱 [Twilio] Sent to {to_phone} | SID: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"  ❌ [Twilio ERROR] Failed to send message to {to_phone}")
        print(f"     Details: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  META CLOUD API SENDER
# ═══════════════════════════════════════════════════════════════

def _send_meta_text(to_phone: str, body: str):
    """Send a text WhatsApp message via Meta Cloud API."""
    try:
        url = f"https://graph.facebook.com/v18.0/{META_PHONE_ID}/messages"
        headers = {"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"}
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("whatsapp:", "")
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "text",
            "text": {"body": body},
        }
        resp = requests.post(url, json=payload, headers=headers)
        
        # This will raise an exception if the status is 4xx or 5xx
        resp.raise_for_status() 
        
        result = resp.json()
        print(f"  📱 [Meta] Text to {to_phone} | Status: {resp.status_code}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"  ❌ [Meta ERROR] Failed to send text to {to_phone}")
        print(f"     Details: {e}")
        if e.response is not None:
            print(f"     API Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"  ❌ [Meta ERROR] Unexpected error: {e}")
        return None


def _send_meta_image(to_phone: str, image_url: str, caption: str):
    """Send an image WhatsApp message via Meta Cloud API."""
    try:
        url = f"https://graph.facebook.com/v18.0/{META_PHONE_ID}/messages"
        headers = {"Authorization": f"Bearer {META_TOKEN}", "Content-Type": "application/json"}
        clean_phone = to_phone.replace("+", "").replace(" ", "").replace("whatsapp:", "")
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        }
        resp = requests.post(url, json=payload, headers=headers)
        
        # Raise HTTPException for bad status codes
        resp.raise_for_status()
        
        result = resp.json()
        print(f"  📱 [Meta] Image to {to_phone} | Status: {resp.status_code}")
        return result
    except requests.exceptions.RequestException as e:
        print(f"  ❌ [Meta ERROR] Failed to send image to {to_phone}")
        print(f"     Details: {e}")
        if e.response is not None:
            print(f"     API Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"  ❌ [Meta ERROR] Unexpected image error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API — MESSAGE TYPES
# ═══════════════════════════════════════════════════════════════

def send_entry_notification(to_phone: str, plate: str, zone_name: str, gate_id: str):
    """Send entry notification with zone routing and dashboard link."""
    body = (
        f"🅿️ *SCET Smart Parking*\n\n"
        f"✅ Vehicle *{plate}* entered via *{gate_id}*\n"
        f"📍 You are assigned to: *{zone_name}*\n\n"
        f"🗺️ Navigate to your zone on the campus map.\n"
        f"🔗 Dashboard: {USER_DASHBOARD}\n\n"
        f"Have a great day! 🎓"
    )
    return _dispatch(to_phone, body)


def send_guardian_alert(to_phone: str, plate: str, gate_id: str, image_url: str = None):
    """
    Send Guardian Mode alert WITH vehicle photo.
    This is the critical anti-theft message.
    """
    body = (
        f"⚠️ *GUARDIAN MODE ALERT*\n\n"
        f"🚨 Unauthorized exit detected!\n"
        f"🚗 Vehicle: *{plate}*\n"
        f"📍 Location: *{gate_id}*\n\n"
        f"If this is YOU, please disable Guardian Mode from your dashboard:\n"
        f"🔗 {USER_DASHBOARD}\n\n"
        f"If this is NOT you, call campus security IMMEDIATELY! 🚔\n"
        f"📞 Security: +91-XXX-XXXX"
    )
    if image_url and _use_twilio():
        return _send_twilio(to_phone, body, media_url=image_url)
    elif image_url and _use_meta():
        return _send_meta_image(to_phone, image_url, body)
    else:
        return _dispatch(to_phone, body)


def send_paging_alert(to_phone: str, blocked_plate: str):
    """Send anonymous paging alert to the owner of a blocking vehicle."""
    body = (
        f"🔔 *Parking Alert — SCET Campus*\n\n"
        f"Your vehicle *{blocked_plate}* is blocking another car.\n"
        f"Please move your vehicle at your earliest convenience.\n\n"
        f"Thank you for your cooperation! 🙏"
    )
    return _dispatch(to_phone, body)


def send_visitor_arrival(to_phone: str, visitor_name: str, visitor_plate: str, gate_id: str):
    """Notify host that their registered visitor has arrived."""
    body = (
        f"👋 *Visitor Arrived — SCET Campus*\n\n"
        f"Your visitor *{visitor_name}* (vehicle: *{visitor_plate}*) "
        f"has arrived at *{gate_id}*.\n\n"
        f"The gate has been opened automatically. ✅"
    )
    return _dispatch(to_phone, body)


def send_exit_notification(to_phone: str, plate: str, duration: str):
    """Send exit confirmation with parking duration."""
    body = (
        f"👋 *SCET Smart Parking — Exit*\n\n"
        f"Vehicle *{plate}* has exited.\n"
        f"⏱️ Duration: *{duration}*\n\n"
        f"See you next time! 🎓"
    )
    return _dispatch(to_phone, body)


# ═══════════════════════════════════════════════════════════════
#  DISPATCHER (auto-selects Twilio vs Meta vs log-only)
# ═══════════════════════════════════════════════════════════════

def _dispatch(to_phone: str, body: str, media_url: str = None):
    """Route message to the configured WhatsApp provider, or log if none configured."""
    if _use_twilio():
        return _send_twilio(to_phone, body, media_url)
    elif _use_meta():
        if media_url:
            return _send_meta_image(to_phone, media_url, body)
        return _send_meta_text(to_phone, body)
    else:
        print(f"  📱 [LOG-ONLY] WhatsApp to {to_phone}:")
        print(f"     {body[:200]}...")
        if media_url:
            print(f"     📎 Image: {media_url}")
        return {"status": "logged", "to": to_phone}
