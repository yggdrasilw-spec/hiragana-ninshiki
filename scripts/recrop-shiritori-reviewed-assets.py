"""Reproduce reviewed contact-sheet extractions without changing source sheets.

Example: python scripts/recrop-shiritori-reviewed-assets.py \
  data/image-coverage/2026-10-12/crop-repairs.json
"""
import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageOps

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("plan", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
plan_path = args.plan if args.plan.is_absolute() else root / args.plan
entries = json.loads(plan_path.read_text(encoding="utf-8"))
prepared = []
seen = set()
for entry in entries:
    name = entry["file"]
    source = Path(entry["sourceSheet"])
    box = entry["cropBox"]
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.png", name) or name in seen:
        raise ValueError(f"Invalid or duplicate filename: {name}")
    if source.is_absolute() or source.parts[0] != "sheets" or ".." in source.parts:
        raise ValueError(f"Invalid source sheet: {source}")
    seen.add(name)
    with Image.open(root / "assets/shiritori" / source) as picture:
        picture = picture.convert("RGB")
        if (len(box) != 4 or not all(type(v) is int for v in box)
                or not 0 <= box[0] < box[2] <= picture.width
                or not 0 <= box[1] < box[3] <= picture.height):
            raise ValueError(f"Invalid crop box: {name}")
        color = picture.getpixel((box[0], box[1]))
        image = ImageOps.pad(picture.crop(box), (256, 256),
                             method=Image.Resampling.LANCZOS, color=color)
        prepared.append((name, image))
for name, image in prepared:
    image.save(root / "assets/shiritori" / name, optimize=True)
print(f"Reproduced {len(prepared)} reviewed 256px assets; source sheets unchanged")
