import os
import requests
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_chat_id():
    """Fetches recently received Telegram messages to get the sender's Chat ID."""
    print("Fetching recent messages sent to your bot...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        
        if not data.get("ok"):
            print("❌ Telegram API returned an error:", data)
            return
            
        messages = data.get("result", [])
        if not messages:
            print("\n⚠️ No messages found! Please send a message (like 'hello') to your bot on Telegram first, then run this script again.")
            return
            
        print("\n✅ Found recent messages! Here are the Chat IDs:\n")
        
        seen_ids = set()
        for msg in messages:
            if "message" in msg:
                chat = msg["message"]["chat"]
                chat_id = chat["id"]
                username = chat.get("username", "Unknown Username")
                first_name = chat.get("first_name", "Unknown Name")
                text = msg["message"].get("text", "[No text]")
                
                if chat_id not in seen_ids:
                    print(f"  👤 {first_name} (@{username})")
                    print(f"  🔑 Chat ID: {chat_id}")
                    print(f"  💬 Last message: '{text}'\n")
                    seen_ids.add(chat_id)
                    
        print("\n👉 Copy the 10-digit 'Chat ID' above and put it in your test_scenarios.py file!")

    except Exception as e:
        print("❌ Failed to connect to Telegram:", e)

if __name__ == "__main__":
    get_chat_id()
