"""Acquire versioned public datasets. Standard library only; no training.

Preserves source archives and receipts. Never executes downloaded content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "data" / "plant"
MAX_BYTES = 2500 * 1024 * 1024
AGENT = "AgroSentinel-academic-data-collection/1.0"


def request(url, headers=None):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": AGENT, **(headers or {})}), timeout=45
    )


def get_json(url, headers=None):
    with request(url, headers) as response:
        return json.load(response)


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Metadata and reports are generated artifacts; never overwrite originals.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def digest(path, algorithm="sha256"):
    hasher = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def download(url, destination, checksum=None, expected_size=None):
    if not destination.exists():
        partial = destination.with_suffix(destination.suffix + ".part")
        if partial.exists():
            raise RuntimeError(f"Partial download exists; inspect it before retry: {partial}")
        with request(url) as response, partial.open("xb") as stream:
            expected = response.headers.get("Content-Length")
            if expected and int(expected) > MAX_BYTES:
                raise RuntimeError("Archive exceeds first-batch size limit")
            count = 0
            next_progress = 64 * 1024 * 1024
            for block in iter(lambda: response.read(1024 * 1024), b""):
                count += len(block)
                if count > MAX_BYTES:
                    raise RuntimeError("Archive exceeds first-batch size limit")
                stream.write(block)
                if count >= next_progress:
                    print(f"  {count // (1024 * 1024)} MB downloaded", flush=True)
                    next_progress += 64 * 1024 * 1024
        if expected and count != int(expected):
            raise RuntimeError("Download length differs from server header")
        if expected_size is not None and count != expected_size:
            raise RuntimeError("Download length differs from repository metadata")
        if checksum:
            algorithm, expected_hash = checksum.split(":", 1)
            if digest(partial, algorithm) != expected_hash:
                raise RuntimeError("Published checksum mismatch; partial file retained")
        partial.rename(destination)
    if checksum:
        algorithm, expected_hash = checksum.split(":", 1)
        if digest(destination, algorithm) != expected_hash:
            raise RuntimeError("Existing archive differs from published checksum")
    if expected_size is not None and destination.stat().st_size != expected_size:
        raise RuntimeError("Existing archive size differs from repository metadata")
    with zipfile.ZipFile(destination) as archive:
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"ZIP integrity failure: {bad}")
    return {"file": str(destination.relative_to(ROOT)), "url": url,
            "bytes": destination.stat().st_size, "sha256": digest(destination),
            "published_checksum": checksum, "zip_integrity": "passed"}


def inventory(archive_path):
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
    with zipfile.ZipFile(archive_path) as archive:
        files = [info for info in archive.infolist() if not info.is_dir()]
        # macOS packaging metadata is not an image observation.
        image_files = [info for info in files if Path(info.filename).suffix.lower() in exts
                       and "__MACOSX/" not in info.filename
                       and not Path(info.filename).name.startswith("._")]
        annotation_files = [info.filename for info in files
                            if Path(info.filename).suffix.lower() in {".csv", ".json", ".txt", ".xml", ".xlsx"}
                            and "__MACOSX/" not in info.filename]
        image_hashes = {}
        for info in image_files:
            content_hash = hashlib.sha256(archive.read(info)).hexdigest()
            image_hashes.setdefault(content_hash, []).append(info.filename)
        return {"archive": str(archive_path.relative_to(ROOT)),
                "image_files": len(image_files), "unique_image_byte_hashes": len(image_hashes),
                "exact_duplicate_groups": [names for names in image_hashes.values() if len(names) > 1],
                "annotation_and_document_files": annotation_files,
                "image_paths": [info.filename for info in image_files],
                "note": "Counts are archive inventory, not expert-reviewed training examples; masks may be counted as image files."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["plantdoc", "potato-uav", "plantwild-v2", "gymnsa"], required=True)
    args = parser.parse_args()
    if args.dataset == "potato-uav":
        metadata = get_json("https://zenodo.org/api/records/10727413")
        folder = ROOT / "originals" / args.dataset / "10727413"
        files = [{"name": f["key"], "url": f["links"]["self"], "checksum": f["checksum"]}
                 for f in metadata["files"] if f["key"].endswith(".zip")]
        if sum(f["size"] for f in metadata["files"]) > MAX_BYTES:
            raise RuntimeError("Dataset exceeds first-batch size limit")
        license_info = metadata["metadata"].get("license")
        source = metadata["links"]["self_html"]
    elif args.dataset == "plantwild-v2":
        repo = "uqtwei2/PlantWild"
        metadata = get_json(f"https://huggingface.co/api/datasets/{repo}")
        sha = metadata["sha"]
        tree = get_json(f"https://huggingface.co/api/datasets/{repo}/tree/{sha}?recursive=true&expand=false")
        archive = next(entry for entry in tree if entry["path"] == "plantwild_v2.zip")
        metadata["download_tree"] = tree
        metadata["pinned_commit"] = sha
        folder = ROOT / "originals" / args.dataset / sha[:12]
        files = [{"name": archive["path"],
                  "url": f"https://huggingface.co/datasets/{repo}/resolve/{sha}/{archive['path']}?download=true",
                  "checksum": "sha256:" + archive["lfs"]["oid"], "size": archive["size"]}]
        license_info = metadata.get("cardData", {}).get("license")
        source = f"https://huggingface.co/datasets/{repo}/tree/{sha}"
    elif args.dataset == "gymnsa":
        source = "https://data.mendeley.com/datasets/44kjgc4gkc/1"
        with request(source, {"User-Agent": "Mozilla/5.0"}) as response:
            page = response.read().decode("utf-8")
        state, _ = json.JSONDecoder().raw_decode(page.split("window.INITIAL_STATE = ", 1)[1])
        snapshot = state["dataset"]["snapshot"]
        if snapshot["id"] != "44kjgc4gkc" or snapshot["version"] != 1:
            raise RuntimeError("Unexpected GYMNSA dataset/version")
        endpoint = "https://data.mendeley.com/public-api/datasets/44kjgc4gkc"
        headers = {"Accept": "application/vnd.mendeley-public-dataset.1+json", "User-Agent": "Mozilla/5.0"}
        folders = get_json(endpoint + "/folders/1", headers)
        if folders:
            raise RuntimeError("GYMNSA repository layout changed; inspect folder files before downloading")
        file_list = get_json(endpoint + "/files?folder_id=root&version=1&%24start=0&%24limit=1000", headers)
        if not isinstance(file_list, list) or not file_list:
            raise RuntimeError("No GYMNSA files returned")
        metadata = {"snapshot": snapshot, "files": file_list, "folders": folders}
        folder = ROOT / "originals" / args.dataset / "1"
        files = [{"name": f["filename"], "url": f["content_details"]["download_url"],
                  "checksum": "sha256:" + f["content_details"]["sha256_hash"],
                  "size": f["content_details"]["size"]}
                 for f in file_list]
        if any(not f["name"].lower().endswith(".zip") for f in files):
            raise RuntimeError("GYMNSA added non-ZIP files; inspect download handling")
        license_info = snapshot["licence"]
    else:
        repo = "pratikkayal/PlantDoc-Object-Detection-Dataset"
        metadata = get_json(f"https://api.github.com/repos/{repo}")
        commit = get_json(f"https://api.github.com/repos/{repo}/commits/{metadata['default_branch']}")
        sha = commit["sha"]
        metadata["pinned_commit"] = sha
        folder = ROOT / "originals" / args.dataset / sha[:12]
        files = [{"name": "PlantDoc-Object-Detection-Dataset.zip",
                  "url": f"https://api.github.com/repos/{repo}/zipball/{sha}", "checksum": None}]
        license_info = metadata.get("license")
        source = metadata["html_url"]
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / "source_metadata.json").exists():
        save_json(folder / "source_metadata.json", metadata)
    receipts, inventories = [], []
    for file in files:
        if Path(file["name"]).name != file["name"]:
            raise RuntimeError("Unsafe source filename")
        target = folder / file["name"]
        print(f"Acquiring {file['name']}...", flush=True)
        receipts.append(download(file["url"], target, file["checksum"], file.get("size")))
        inventories.append(inventory(target))
        print(f"Verified {target.name}: {inventories[-1]['image_files']} image files", flush=True)
    report = {"dataset": args.dataset, "collected_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": source, "license_metadata": license_info, "downloads": receipts,
              "inventory": inventories, "training_status": "not_prepared_or_split"}
    report_path = folder / "acquisition_receipt.json"
    if not report_path.exists():
        save_json(report_path, report)
    print(f"Receipt: {report_path}", flush=True)


if __name__ == "__main__":
    main()
