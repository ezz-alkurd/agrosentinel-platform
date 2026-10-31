"""Record a verified experiment's manifests/config checksums without changing its splits."""
import argparse
import hashlib
import json
from datetime import datetime, timezone

from prepare_public import ROOT, write_json


def freeze(version):
    folder = ROOT / "prepared" / version
    target = folder / "experiment_freeze.json"
    if target.exists():
        raise RuntimeError("Already frozen: use a new version for changed labels or splits")
    verification = json.loads((folder / "verification.json").read_text(encoding="utf-8"))
    if not verification["passed"]:
        raise RuntimeError("Cannot freeze an export with failed verification")
    files = [folder / name for name in ("training_manifest.jsonl", "inventory.jsonl", "label_catalog.json",
             "preparation_report.json", "review_queue.jsonl", "mechanical_actions.jsonl", "near_duplicate_candidates.jsonl")]
    files += list(folder.glob("*/labels.json")) + list(folder.glob("*/data.yaml"))
    # Annotation hashes plus image hashes in the training manifest protect the actual export too.
    files += list(folder.glob("*/labels/*/*.txt"))
    checksums = {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in sorted(files)}
    write_json(target, {"version": version, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                       "files_sha256": checksums, "verified_images": verification["verified_images"],
                       "policy": "No training or test evaluation performed. New labels/splits require a new version. Local absolute config paths may be regenerated for relocation, with verification and a new location-specific checksum record."})
    print(f"Frozen {version}: {len(checksums)} manifest/config/annotation files; image hashes retained in manifest")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    if not args.version or not all(c.isalnum() or c in "_-" for c in args.version):
        parser.error("Use a simple version directory name")
    freeze(args.version)
