"""
cleanup_firebase.py — delete all detection data from Firebase.

Removes:
  - every document in the Firestore `events` collection (what the app's
    Events / Alerts / Map pages show)
  - every image under `detections/` in Firebase Storage

⚠️  THIS IS PERMANENT. There is no undo. Run only when you want a clean slate.

USAGE (from D:\\graduation-project):
    py ai-backend/cleanup_firebase.py            # asks you to type DELETE to confirm
    py ai-backend/cleanup_firebase.py --yes      # skip the prompt (careful)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from firebase_config import initialize_firebase


def delete_events(db) -> int:
    count = 0
    coll = db.collection("events")
    while True:
        docs = list(coll.limit(400).stream())
        if not docs:
            break
        batch = db.batch()
        for d in docs:
            batch.delete(d.reference)
        batch.commit()
        count += len(docs)
        print(f"  deleted {count} event docs...")
    return count


def delete_storage(bucket) -> int:
    blobs = list(bucket.list_blobs(prefix="detections/"))
    for b in blobs:
        b.delete()
    return len(blobs)


def main() -> None:
    skip_prompt = "--yes" in sys.argv

    print("This will PERMANENTLY delete:")
    print("  - all Firestore `events` documents")
    print("  - all `detections/` images in Storage")
    if not skip_prompt:
        ans = input('Type "DELETE" to confirm: ').strip()
        if ans != "DELETE":
            print("Cancelled.")
            return

    db, bucket = initialize_firebase()
    print("\nDeleting Firestore events...")
    n_events = delete_events(db)
    print("Deleting Storage images...")
    n_files = delete_storage(bucket)

    print(f"\n✅ Done. Removed {n_events} events and {n_files} images.")
    print("The app's Events / Alerts / Map will be empty until new detections upload.")


if __name__ == "__main__":
    main()
