"""Move MP4 metadata before media without re-encoding video or audio.
Usage: python scripts/make_mp4_faststart.py original.mp4 optimized.mp4
Only conventional, non-fragmented MP4 files are supported. Originals stay intact.
"""
import argparse
import hashlib
import struct
from pathlib import Path

CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf"}

def atoms(data, start=0, end=None):
    end = len(data) if end is None else end
    while start < end:
        if end - start < 8:
            raise ValueError("Truncated MP4 atom")
        size, kind = struct.unpack_from(">I4s", data, start)
        header = 8
        if size == 1:
            size = struct.unpack_from(">Q", data, start + 8)[0]
            header = 16
        elif size == 0:
            size = end - start
        if size < header or start + size > end:
            raise ValueError("Invalid MP4 atom size")
        yield start, size, kind, header
        start += size

def optimize(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError("Use a separate output file")
    data = source.read_bytes()
    top = list(atoms(data))
    if any(kind == b"moof" for _, _, kind, _ in top):
        raise ValueError("Fragmented MP4 is not supported")
    moovs = [a for a in top if a[2] == b"moov"]
    mdats = [a for a in top if a[2] == b"mdat"]
    if len(moovs) != 1 or not mdats:
        raise ValueError("Expected one moov and at least one mdat")
    moov_start, moov_size, _, _ = moovs[0]
    insertion = min(a[0] for a in mdats)
    if moov_start < insertion:
        destination.write_bytes(data)
        return {"already_faststart": True, "bytes": len(data)}
    metadata = bytearray(data[moov_start:moov_start+moov_size])
    offset_count = 0
    def patch(start, end):
        nonlocal offset_count
        for pos, size, kind, header in atoms(metadata, start, end):
            body = pos + header
            if kind in CONTAINERS:
                patch(body, pos + size)
            elif kind in (b"stco", b"co64"):
                count = struct.unpack_from(">I", metadata, body+4)[0]
                fmt, width = (">I", 4) if kind == b"stco" else (">Q", 8)
                if body+8+count*width > pos+size:
                    raise ValueError("Truncated chunk offset table")
                for i in range(count):
                    location = body+8+i*width
                    old = struct.unpack_from(fmt, metadata, location)[0]
                    new = old + moov_size if insertion <= old < moov_start else old
                    struct.pack_into(fmt, metadata, location, new)
                    offset_count += 1
    patch(0, len(metadata))
    if not offset_count:
        raise ValueError("No chunk offset tables found")
    result = data[:insertion] + metadata + data[insertion:moov_start] + data[moov_start+moov_size:]
    if len(result) != len(data):
        raise ValueError("Remux changed file size unexpectedly")
    after = list(atoms(result))
    original_payload = [hashlib.sha256(data[p+h:p+s]).hexdigest() for p,s,k,h in top if k == b"mdat"]
    new_payload = [hashlib.sha256(result[p+h:p+s]).hexdigest() for p,s,k,h in after if k == b"mdat"]
    if original_payload != new_payload:
        raise ValueError("Media payload changed")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(result)
    return {"already_faststart": False, "bytes": len(result), "chunk_offsets_updated": offset_count, "media_payload_unchanged": True}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    print(optimize(args.source, args.destination))
