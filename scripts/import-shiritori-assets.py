"""Import reviewed per-agent image batches into the shiritori data files.

Each CSV requires reading,word,filename,scene,sourceSheet,tileIndex,generatedAt.
For entries sharing reading and word, supply the vocabulary row id (1-based,
excluding the header) or an exact meaning to avoid assigning to another sense.
Paths are resolved from the repository root, regardless of the working directory.
All batches are checked before either shared data file is changed.
"""
import argparse
import csv
import json
import re
import hashlib
import importlib.util
from pathlib import Path

from PIL import Image


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("batches", nargs="+", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('shiritori_grid', root / 'scripts/crop-shiritori-grid.py')
grid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grid)
validated_sheets = {}
csv_path = root / "whitelist.csv"
before_text = csv_path.read_text(encoding="utf-8")
manifest_path = root / "assets/shiritori/manifest.json"
with csv_path.open(encoding="utf-8-sig", newline="") as stream:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames
    rows = list(reader)
lookup = {}
for row in rows:
    lookup.setdefault((row["reading"], row["word"]), []).append(row)
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
ledger_path = root / "data/corrections/2026-10-11-ledger.json"
original_ids = json.loads(ledger_path.read_text(encoding="utf-8"))["currentOriginalIds"] if ledger_path.is_file() else []
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
            matches = lookup.get(key, [])
            if item.get("id"):
                row_id = int(item["id"])
                if not 1 <= row_id <= len(rows):
                    raise ValueError(f"Invalid vocabulary row ID: {row_id}")
                row = rows[row_id - 1]
                if (row["reading"], row["word"]) != key or (item.get("meaning") and item["meaning"] != row["meaning"]):
                    raise ValueError(f"Vocabulary row does not match batch: {row_id} / {key}")
            else:
                if item.get("meaning"):
                    matches = [row for row in matches if row["meaning"] == item["meaning"]]
                if len(matches) != 1:
                    raise ValueError(f"Word missing or ambiguous; supply id or meaning: {key}")
                row = matches[0]
                row_id = next(i for i, candidate in enumerate(rows, 1) if candidate is row)
            if row_id in seen_words or filename in seen_files:
                raise ValueError(f"Duplicate in supplied batches: {key} / {filename}")
            seen_words.add(row_id)
            seen_files.add(filename)
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
            credit = item.get('credit') or 'AI生成イラスト'
            if credit not in ('AI生成イラスト', 'プログラム生成図'):
                raise ValueError('Invalid generation credit: ' + filename)
            tile = int(item["tileIndex"])
            if tile < 1:
                raise ValueError(f"Invalid tile index: {tile}")
            evidence = None
            evidence_path = item.get('cropValidation', '')
            if date >= '2026-10-12' and not evidence_path and not any(
                    tag in Path(sheet).stem for tag in ('single-', 'diagram-')):
                raise ValueError('New contact-sheet assets require cropValidation evidence: ' + filename)
            if evidence_path:
                report_path = (root / evidence_path).resolve()
                if not report_path.is_relative_to(root) or not report_path.is_file():
                    raise ValueError('Invalid crop-validation report path')
                cache_key = (str(report_path), str(sheet_path))
                if cache_key not in validated_sheets:
                    validated_sheets[cache_key] = grid.verify_report(report_path, sheet_path, root / 'assets/shiritori')
                evidence = validated_sheets[cache_key].get(filename)
                if not evidence or evidence['tileIndex'] != tile:
                    raise ValueError('Filename or tile index differs from validated grid: ' + filename)
                if not filename.endswith(f'-word-{row_id}.png'):
                    raise ValueError('Validated tile filename must end in its vocabulary row ID: ' + filename)
            pending.append((row, asset_path, {
                "reading": key[0], "word": key[1], "meaning": row["meaning"],
                "file": filename, "mode": "asset", "credit": credit,
                "prompt": item.get("prompt") or f"Children's picture-book contact sheet, tile {tile}: {scene}. Warm watercolor style, no text, no watermark.",
                "review": f"目視確認済み: {scene}", "status": "reviewed",
                "generatedAt": date, "sourceSheet": sheet, "tileIndex": tile,
                **({'cropValidation': evidence_path, 'cropBox': evidence['cropBox'],
                    'cropMethod': json.loads(report_path.read_text(encoding='utf-8'))['method'], 'sha256': evidence['sha256'],
                    'cropChecks': evidence} if evidence else {}),
                "aliases": [{
                    "id": row_id,
                    "originalId": original_ids[row_id - 1] if row_id <= len(original_ids) else None,
                    "reading": key[0], "word": key[1], "meaning": row["meaning"],
                    "reuseReason": "語義に合わせて新規生成した専用画像。",
                    "sourceReview": f"目視確認済み: {scene}",
                }],
            }))
for row, asset_path, asset in pending:
    row["image_asset"] = asset_path
    row["image_mode"] = "asset"
    row["image_credit"] = asset['credit']
    manifest["assets"].append(asset)
if pending:
    history_path = root / "data/dictionary-imports/history.json"
    history = None
    if ledger_path.is_file():
        history = json.loads(history_path.read_text(encoding="utf-8")) if history_path.is_file() else []
        expected_hash = history[-1]["afterSha256"] if history else json.loads(ledger_path.read_text(encoding="utf-8"))["afterSha256"]
        if hashlib.sha256(before_text.encode()).hexdigest() != expected_hash:
            raise ValueError("Dictionary changed outside recorded imports.")
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if history is not None:
        after_text = csv_path.read_text(encoding="utf-8")
        history.append({
            "type": "image-assets",
            "batches": [str(p.resolve().relative_to(root)) if p.is_absolute() and p.is_relative_to(root) else str(p) for p in args.batches],
            "beforeSha256": hashlib.sha256(before_text.encode()).hexdigest(),
            "afterSha256": hashlib.sha256(after_text.encode()).hexdigest(),
            "modifiedLines": [{"id": i, "before": before, "after": after}
                              for i, (before, after) in enumerate(zip(before_text.splitlines()[1:], after_text.splitlines()[1:]), 1)
                              if before != after],
        })
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Imported {len(pending)} assets; total {len(manifest['assets'])}")
