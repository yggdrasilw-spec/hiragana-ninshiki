"""Apply the supplied 75-order review, preserving unrelated fields and lineage.

Run only on the recorded starting CSV; later edits must not be overwritten.
"""
import csv
import hashlib
import json
import shutil
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/corrections'
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def sha(blob):
    return hashlib.sha256(blob).hexdigest()

ledger_path = BASE / '2026-10-12-word-image-ledger.json'
csv_path = ROOT / 'whitelist.csv'
before_blob = csv_path.read_bytes()
if ledger_path.exists():
    assert sha(before_blob) == read(ledger_path)['afterSha256'], 'Later edits exist; do not reapply.'
    print('Already applied; recorded CSV matches.')
    raise SystemExit(0)
assert sha(before_blob) == 'e683c6984bed3ae64c32833e451b4220d7c672073602186d998d55d99e53c9c4', 'Starting CSV changed.'
plan = read(BASE / '2026-10-12-word-image-plan.json')
groups = read(BASE / '2026-10-12-word-image-generated.json')
with csv_path.open(encoding='utf-8', newline='') as stream:
    reader = csv.DictReader(stream)
    fields = reader.fieldnames
    before = list(reader)
rows = [dict(r) for r in before]
manifest_path = ROOT / 'assets/shiritori/manifest.json'
manifest = read(manifest_path)
assets = {a['file']: a for a in manifest['assets']}
image_edits = {}
for entry in read(ROOT / 'data/image-coverage/2026-10-12/word-image-crop-repairs.json'):
    a = assets[entry['file']]
    a.update(sourceType='recropped-generated-sheet', cropBox=entry['cropBox'],
             lastCorrectedAt=plan['date'], review='目視確認済み: 元シートのコマ内のみを抽出。必要な絵の欠けと隣コマ混入を修正。')
    image_edits[entry['file']] = {'action': 'recrop', **entry}
for group in groups:
    sheet = ROOT / 'assets/shiritori/sheets' / group['file']
    if not sheet.exists():
        shutil.copyfile(group['source'], sheet)
    with Image.open(sheet) as picture:
        picture = picture.convert('RGB')
        cols, nrows = group['grid']
        for index, before_id in enumerate(group['ids']):
            file = Path(rows[before_id - 1]['image_asset']).name
            cw, ch = picture.width / cols, picture.height / nrows
            col, row = index % cols, index // cols
            box = [round(col*cw+6), round(row*ch+6), round((col+1)*cw-6), round((row+1)*ch-6)]
            image = ImageOps.pad(picture.crop(box), (256, 256), method=Image.Resampling.LANCZOS, color=(255, 253, 247))
            image.save(ROOT / 'assets/shiritori' / file, optimize=True)
            a = assets[file]
            a.update(sourceType='generated-sheet', sourceSheet='sheets/'+group['file'],
                     tileIndex=index+1, cropBox=box, sheetSize=list(picture.size), grid=group['grid'],
                     prompt=group['prompt'], generatedAt=plan['date'], lastCorrectedAt=plan['date'],
                     review=group.get('reviews', {}).get(str(before_id), '目視確認済み: '+rows[before_id-1]['word']+'の注文に沿って構造・内容を修正。'),
                     status='reviewed')
            image_edits[file] = {'action': 'regenerate', 'beforeId': before_id,
                                'sourceSheet': a['sourceSheet'], 'cropBox': box, 'review': a['review']}
for before_id, meaning in plan['meanings'].items():
    rows[int(before_id)-1]['meaning'] = meaning
removed = {m['drop']: m for m in plan['merges']}
origins = [i for i in range(1, len(rows)+1) if i not in removed]
current = [rows[i-1] for i in origins]
new_ids = {old: new for new, old in enumerate(origins, 1)}
uses = {}
for old in origins:
    row = rows[old-1]
    if row['image_asset']:
        uses.setdefault(Path(row['image_asset']).name, []).append((old, row))
new_assets = []
for file, references in uses.items():
    a = assets[file]
    if file in image_edits:
        a['sha256'] = sha((ROOT / 'assets/shiritori' / file).read_bytes())
    _, primary = next(((i, r) for i, r in references if (r['reading'], r['word']) == (a.get('reading'), a.get('word'))), references[0])
    a.update({k: primary[k] for k in ['reading', 'word', 'meaning']})
    old_aliases = {(v['reading'], v['word']): v for v in a.get('aliases', [])}
    aliases = []
    for old, row in references:
        alias = dict(old_aliases.get((row['reading'], row['word']), {}))
        alias.update(id=new_ids[old], **{k: row[k] for k in ['reading', 'word', 'meaning']})
        alias.setdefault('originalId', old)
        if file in image_edits:
            alias.update(reuseReason='今回の共有先全語義との対応を確認。', sourceReview=a['review'])
        aliases.append(alias)
    a['aliases'] = aliases
    new_assets.append(a)
manifest.update(assets=new_assets, lastCorrectedAt=plan['date'])
coverage_path = ROOT / 'data/image-coverage/review-2026-10-10.json'
coverage = read(coverage_path)
new_coverage = []
for old in origins:
    row = rows[old-1]
    entry = dict(coverage[old-1])
    entry.update(id=new_ids[old], **{k: row[k] for k in ['reading','word','meaning','level','image_asset']})
    if str(old) in plan['meanings'] or Path(row['image_asset']).name in image_edits:
        entry['wordImage75Review'] = {'date': plan['date'], 'beforeId': old,
            'wordReading': '未確認',
            'meaning': '今回修正' if str(old) in plan['meanings'] else '未確認',
            'image': '今回目視確認・修正' if Path(row['image_asset']).name in image_edits else '維持・未確認'}
    new_coverage.append(entry)
with csv_path.open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(current)
changes = []
for old, (a, b) in enumerate(zip(before, rows), 1):
    if old in removed:
        merge = removed[old]
        changes.append({'beforeId': old, 'action': 'delete', 'before': a,
                        'mergedIntoBeforeId': merge['keep'], 'mergedIntoId': new_ids[merge['keep']], 'reason': merge['reason']})
    elif a != b:
        changes.append({'beforeId': old, 'id': new_ids[old], 'action': 'edit', 'before': a, 'after': b})
record = {'type': 'reviewed-corrections', 'date': plan['date'], 'request': plan['request'],
          'beforeSha256': sha(before_blob), 'afterSha256': sha(csv_path.read_bytes()),
          'sourceRows': len(before), 'currentRows': len(current), 'currentBeforeIds': origins, 'changes': changes}
history_path = ROOT / 'data/dictionary-imports/history.json'
history = read(history_path)
assert history[-1]['afterSha256'] == record['beforeSha256']
history.append(record)
write(history_path, history)
write(ledger_path, {**record, 'imageEdits': image_edits, 'removedManifestAssets': sorted(set(assets)-set(uses))})
write(manifest_path, manifest)
write(coverage_path, new_coverage)
print(json.dumps({'rows': len(current), 'meaningEdits': len(plan['meanings']), 'merges': len(removed), 'imageEdits': len(image_edits)}, ensure_ascii=False))
