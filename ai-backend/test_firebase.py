from firebase_config import initialize_firebase
from datetime import datetime, UTC

db, bucket = initialize_firebase()

# -------------------------
# Test Firestore
# -------------------------
test_doc = {
    "message": "Firebase connection successful",
    "created_at": datetime.now(UTC).isoformat()
}

db.collection("test_events").add(test_doc)
print("Firestore test successful")

# -------------------------
# Test Storage
# -------------------------
with open("sample.txt", "w") as f:
    f.write("Hello from AgroSentinel")

blob = bucket.blob("test/sample.txt")
blob.upload_from_filename("sample.txt")

print("Storage upload successful")
print("Uploaded to:", blob.name)