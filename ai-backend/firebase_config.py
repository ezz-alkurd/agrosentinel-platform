import os
import firebase_admin
from firebase_admin import credentials, firestore, storage


def initialize_firebase():
    """
    Initialize Firebase Admin SDK once and return Firestore + Storage clients.
    """
    if not firebase_admin._apps:
        # Resolve the key next to THIS file, so scripts work from any directory.
        default_key = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json"
        )
        private_key = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".secrets", "serviceAccountKey.json")
        key_path = os.getenv("FIREBASE_KEY_PATH") or (private_key if os.path.isfile(private_key) else default_key)

        if not os.path.exists(key_path):
            raise FileNotFoundError(
                f"Firebase key file not found: {key_path}\n"
                f"Set FIREBASE_KEY_PATH or place serviceAccountKey.json in the project folder."
            )

        cred = credentials.Certificate(key_path)

        firebase_admin.initialize_app(cred, {
            "httpTimeout": 10,
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "agriculture-drone-e0dc0.firebasestorage.app")
        })

    db = firestore.client()
    bucket = storage.bucket()
    return db, bucket