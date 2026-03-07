"""
Telegram Notification Service
Sends entry notifications, guardian alerts with images, paging alerts, and visitor arrivals via a Telegram Bot.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Telegram config ──
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ── App URLs ──
USER_DASHBOARD = os.getenv("USER_DASHBOARD_URL", "http://localhost:5174")
ADMIN_DASHBOARD = os.getenv("ADMIN_DASHBOARD_URL", "http://localhost:5173")


def _send_telegram_text(chat_id: str, text: str):
    """Send a text message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"  📱 [LOG-ONLY] Telegram to {chat_id}:\n     {text[:200]}...")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print(f"  📱 [Telegram] Sent text to {chat_id} | Status: {resp.status_code}")
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  ❌ [Telegram ERROR] Failed to send text to {chat_id}")
        if e.response is not None:
            print(f"     API Response: {e.response.text}")
        return None


def _send_telegram_photo(chat_id: str, photo_url: str, caption: str):
    """Send a photo message via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        print(f"  📱 [LOG-ONLY] Telegram Image to {chat_id}:\n     {caption[:200]}...\n     📎 {photo_url}")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        print(f"  📱 [Telegram] Sent image to {chat_id} | Status: {resp.status_code}")
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  ❌ [Telegram ERROR] Failed to send image to {chat_id}")
        if e.response is not None:
            print(f"     API Response: {e.response.text}")
        return None


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API — MESSAGE TYPES
# ═══════════════════════════════════════════════════════════════

def send_entry_notification(chat_id: str, plate: str, zone_name: str, gate_id: str, nav_link: str = None):
    """Send entry notification with zone routing and dashboard link."""
    nav_text = f"🗺️ <a href='{nav_link}'>Click here to navigate to your zone on Google Maps</a>" if nav_link else "🗺️ Navigate to your zone on the campus map."
    body = (
        f"🅿️ <b>SCET Smart Parking</b>\n\n"
        f"✅ Vehicle <b>{plate}</b> entered via <b>{gate_id}</b>\n"
        f"📍 You are assigned to: <b>{zone_name}</b>\n\n"
        f"{nav_text}\n"
        f"🔗 Dashboard: {USER_DASHBOARD}\n\n"
        f"Have a great day! 🎓"
    )
    return _send_telegram_text(chat_id, body)


def send_guardian_alert(chat_id: str, plate: str, gate_id: str, image_url: str = None):
    """
    Send Guardian Mode alert WITH vehicle photo.
    This is the critical anti-theft message.
    """
    body = (
        f"⚠️ <b>GUARDIAN MODE ALERT</b>\n\n"
        f"🚨 Unauthorized exit detected!\n"
        f"🚗 Vehicle: <b>{plate}</b>\n"
        f"📍 Location: <b>{gate_id}</b>\n\n"
        f"If this is YOU, please disable Guardian Mode from your dashboard:\n"
        f"🔗 {USER_DASHBOARD}\n\n"
        f"If this is NOT you, call campus security IMMEDIATELY! 🚔\n"
        f"📞 Security: +91-XXX-XXXX"
    )
    if image_url:
        return _send_telegram_photo(chat_id, image_url, body)
    else:
        return _send_telegram_text(chat_id, body)


def send_paging_alert(chat_id: str, blocked_plate: str):
    """Send anonymous paging alert to the owner of a blocking vehicle."""
    body = (
        f"🔔 <b>Parking Alert — SCET Campus</b>\n\n"
        f"Your vehicle <b>{blocked_plate}</b> is blocking another car.\n"
        f"Please move your vehicle at your earliest convenience.\n\n"
        f"Thank you for your cooperation! 🙏"
    )
    return _send_telegram_text(chat_id, body)


def send_visitor_arrival(chat_id: str, visitor_name: str, visitor_plate: str, gate_id: str):
    """Notify host that their registered visitor has arrived."""
    body = (
        f"👋 <b>Visitor Arrived — SCET Campus</b>\n\n"
        f"Your visitor <b>{visitor_name}</b> (vehicle: <b>{visitor_plate}</b>) "
        f"has arrived at <b>{gate_id}</b>.\n\n"
        f"The gate has been opened automatically. ✅"
    )
    return _send_telegram_text(chat_id, body)


def send_exit_notification(chat_id: str, plate: str, duration: str):
    """Send exit confirmation with parking duration."""
    body = (
        f"👋 <b>SCET Smart Parking — Exit</b>\n\n"
        f"Vehicle <b>{plate}</b> has exited.\n"
        f"⏱️ Duration: <b>{duration}</b>\n\n"
        f"See you next time! 🎓"
    )
    return _send_telegram_text(chat_id, body)
