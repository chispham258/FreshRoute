"""
Firebase Admin SDK setup for Firestore.
Used for: store weights, bundle cache, user context.
"""

import os
from typing import Optional

_firestore_client = None


def get_firestore_client():
    """Lazy-init Firestore client. Returns None if Firebase not configured."""
    global _firestore_client

    if _firestore_client is not None:
        return _firestore_client

    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "")
    if not creds_path or not os.path.exists(creds_path):
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)

        _firestore_client = firestore.client()
        return _firestore_client
    except Exception:
        return None
