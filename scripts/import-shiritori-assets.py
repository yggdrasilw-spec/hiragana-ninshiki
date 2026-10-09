"""Import reviewed per-agent image batches into the shiritori data files.

Each CSV requires reading,word,filename,scene,sourceSheet,tileIndex,generatedAt.
Paths are resolved from the repository root, regardless of the working directory.
All batches are checked before either shared data file is changed.
"""
import argparse
import csv
import json
import re
from pathlib import Path

from PIL import Image


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("batches", nargs="+", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
csv_path = root / "whitelist.csv"
manifest_path = root / "assets/shiritori/manifest.json"
with csv_path.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames
    rows = list(reader)
lookup = {(row["reading"], row["word"]): row for row in rows}
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
registered = {asset["file"]: asset for asset in manifest["assets"]}
pending = []
seen_words = set()
seen_files = set()
for batch_path in args.batches:
    if not batch_path.is_absolute():
        batch_path = root / batch_path
    with batch_path.open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            key = (item["reading"], item["word"])
            filename = item["filename"]
            if not filename.endswith(".png"):
                filename += ".png"
            if not re.fullmatch(r"[a-zA-Z0-9_-]+\.png", filename):
                raise ValueError(f"Invalid asset filename: {filename}")
            if key in seen_words or filename in seen_files:
                raise ValueError(f"Duplicate in supplied batches: {key} / {filename}")
            seen_words.add(key)
            seen_files.add(filename)
            if key not in lookup:
                raise ValueError(f"Word missing from whitelist: {key}")
            row = lookup[key]
            asset_path = f"assets/shiritori/{filename}"
            if row.get("image_asset"):
                if row["image_asset"] == asset_path and filename in registered:
                    continue
                raise ValueError(f"Word already has another image: {key}")
            if filename in registered:
                raise ValueError(f"Filename already registered: {filename}")
            with Image.open(root / asset_path) as picture:
                if picture.size != (256, 256):
                    raise ValueError(f"Expected 256px square: {filename}")
            sheet = item["sourceSheet"]
            sheet_path = root / "assets/shiritori" / sheet
            if not sheet.startswith("sheets/") or ".." in Path(sheet).parts or not sheet_path.is_file():
                raise ValueError(f"Invalid or missing source sheet: {sheet}")
            date = item["generatedAt"]
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                raise ValueError(f"Invalid generation date: {date}")
            scene = item["scene"]
            tile = int(item["tileIndex"])
            if tile < 1:
                raise ValueError(f"Invalid tile index: {tile}")
            pending.append((row, asset_path, {
                "reading": key[0], "word": key[1], "meaning": row["meaning"],
                "file": filename, "mode": "asset", "credit": "AI生成イラスト",
                "prompt": item.get("prompt") or f"Children's picture-book contact sheet, tile {tile}: {scene}. Warm watercolor style, no text, no watermark.",
                "review": f"目視確認済み: {scene}", "status": "reviewed",
                "generatedAt": date, "sourceSheet": sheet, "tileIndex": tile,
            }))
for row, asset_path, asset in pending:
    row["image_asset"] = asset_path
    row["image_mode"] = "asset"
    row["image_credit"] = "AI生成イラスト"
    manifest["assets"].append(asset)
if pending:
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Imported {len(pending)} assets; total {len(manifest['assets'])}")
