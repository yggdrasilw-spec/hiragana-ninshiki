"""Persist image candidates, prioritizing meanings that benefit from scenes.

This estimates search difficulty from the vocabulary; it does not assert that
Wikimedia lacks an image. Existing agent reservations are retained in the list.
"""
import csv
import re
from pathlib import Path

root = Path(__file__).resolve().parent.parent
with (root / "whitelist.csv").open(encoding="utf-8-sig", newline="") as stream:
    vocabulary = list(csv.DictReader(stream))
lookup = {(row["reading"], row["word"]): row for row in vocabulary}
reserved = {}
for batch in sorted((root / "data/batches").glob("agent-*.csv")):
    with batch.open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            reserved[(item["reading"], item["word"])] = batch.name

def classify(row):
    text = row["word"] + " " + row["meaning"]
    if re.search(r"ポケモン|プリキュア|ガンダム|登場人物|登場する|キャラクター|首相|大統領|神話|戦国|武将|幕府|歴史|アニメ|モビルスーツ", text):
        return None
    if re.search(r"気持ち|感情|態度|考え|心配|関係|思う|感じ|性格|様子|状態|能力|性質|信じ|悩|気分|判断", text):
        return (1, "抽象的な意味を場面で伝える候補")
    if re.search(r"[うくぐすつぬぶむる]$", row["word"]) and re.search(r"こと|する|動|手|体", row["meaning"]):
        return (2, "動作を場面で伝える候補")
    if re.search(r"相手|友達|友だち|人と|会話|お話|順番|約束|協力|人に|相互|お互い", text):
        return (2, "人との関わりを場面で伝える候補")
    return None

candidates = []
for key, row in lookup.items():
    batch = reserved.get(key, "")
    if batch:
        priority, reason = 1, "サブエージェント選定済み"
    else:
        if row.get("image_asset") or row.get("level") not in {"1", "2"}:
            continue
        result = classify(row)
        if result is None:
            continue
        priority, reason = result
    status = "registered" if row.get("image_asset") else "assigned" if batch else "candidate"
    candidates.append({"reading":key[0], "word":key[1], "meaning":row["meaning"],
                       "priority":priority, "reason":reason, "status":status, "batch":batch})
candidates.sort(key=lambda item: (not bool(item["batch"]), item["priority"], item["reading"], item["word"]))
candidates = candidates[:240]
path = root / "data/shiritori-image-candidates.csv"
with path.open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["reading","word","meaning","priority","reason","status","batch"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(candidates)
print(f"Wrote {len(candidates)} candidates and reservations to {path.name}")
