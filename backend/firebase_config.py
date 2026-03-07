"""
Firebase Admin SDK Configuration
Initializes the Firebase connection and exposes the `db` reference.
"""

import os
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

load_dotenv()

_CRED_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "serviceAccountKey.json")
_DB_URL = os.getenv("FIREBASE_DATABASE_URL")

if not _DB_URL:
    raise ValueError(
        "FIREBASE_DATABASE_URL is not set. "
        "Copy .env.example to .env and fill in your Firebase project URL."
    )

# Initialize only once
if not firebase_admin._apps:
    cred = credentials.Certificate(_CRED_PATH)
    firebase_admin.initialize_app(cred, {"databaseURL": _DB_URL})


def get_db():
    """Return the Firebase RTDB reference."""
    return db.reference()


def ref(path: str):
    """Shortcut: get a Firebase RTDB reference at the given path."""
    return db.reference(path)
