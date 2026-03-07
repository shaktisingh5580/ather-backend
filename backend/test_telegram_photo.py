import os
import requests
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Diya's chat ID from the test scenario
CHAT_ID = "1626712374"
# The default image URL test scenarios pushes
PHOTO_URL = "https://res.cloudinary.com/demo/image/upload/v1/samples/car.jpg"

def test_photo():
    print(f"Testing Telegram sendPhoto to {CHAT_ID}...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": PHOTO_URL,
        "caption": "Test Guardian Photo"
    }
    
    resp = requests.post(url, json=payload)
    print("Status:", resp.status_code)
    print("Response:", resp.text)

if __name__ == "__main__":
    test_photo()
