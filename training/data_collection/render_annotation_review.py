"""Render mechanical ground-box adjustments for visual review, without changing exports."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[2] / "data" / "plant" / "prepared"


def render(version):
    folder = ROOT / version
    actions = [json.loads(line) for line in (folder / "mechanical_actions.jsonl").read_text(encoding="utf-8").splitlines()]
    action_map = {a["id"]: a for a in actions if a["action"] != "clip_small_boundary_excursion"}
    manifest = [json.loads(line) for line in (folder / "training_manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    selected = [r for r in manifest if r["id"] in action_map]
    columns = 2
    cell_width, cell_height = 620, 470
    canvas = Image.new("RGB", (columns * cell_width, max(1, (len(selected) + 1) // columns) * cell_height), "white")
    draw = ImageDraw.Draw(canvas)
    for i, row in enumerate(selected):
        with Image.open(folder / row["export_path"]) as source:
            photo = ImageOps.exif_transpose(source).convert("RGB")
            photo.thumbnail((600, 380))
        x, y = (i % columns) * cell_width + 10, (i // columns) * cell_height + 10
        canvas.paste(photo, (x, y))
        for b in row["prepared_boxes"]:
            x1, y1, x2, y2 = b["xyxy"]
            draw.rectangle((x+x1*photo.width, y+y1*photo.height, x+x2*photo.width, y+y2*photo.height), outline="red", width=2)
        title = Path(row["archive_member"]).name.encode("ascii", "replace").decode()
        draw.text((x, y+385), title[:80], fill="black")
        draw.text((x, y+405), action_map[row["id"]]["action"], fill="black")
        draw.text((x, y+425), "Geometry QA only; disease identity not verified", fill="black")
    target = folder / "annotation_review.png"
    canvas.save(target)
    print(f"{target}: {len(selected)} adjusted images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1")
    args = parser.parse_args()
    if not args.version or not all(c.isalnum() or c in "_-" for c in args.version):
        parser.error("Use a simple version directory name")
    render(args.version)
