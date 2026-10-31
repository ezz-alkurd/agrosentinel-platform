import firebase_admin
from firebase_admin import credentials, firestore, storage


def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(
            cred,
            {
                "storageBucket": "agrosentinel-storage-2026",
            },
        )

    db = firestore.client()
    bucket = storage.bucket()
    return db, bucket
