"""Verify the 75-order review against its immutable before-state and live data."""
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
def read(file):
    return json.loads((ROOT / file).read_text())
def digest(blob):
    return hashlib.sha256(blob).hexdigest()
plan = read('data/corrections/2026-10-12-word-image-plan.json')
ledger = read('data/corrections/2026-10-12-word-image-ledger.json')
blob = (ROOT / 'whitelist.csv').read_bytes()
rows = list(csv.DictReader(io.StringIO(blob.decode())))
assert digest(blob) == ledger['afterSha256']
assert len(rows) == ledger['sourceRows'] - 3 == 6547
origin = dict(zip(ledger['currentBeforeIds'], rows))
for old, meaning in plan['meanings'].items():
    assert origin[int(old)]['meaning'] == meaning
for merge in plan['merges']:
    assert merge['drop'] not in origin and merge['keep'] in origin
assert [r['word'] for r in rows if r['reading'] == 'かえる'] == ['カエル', '帰る']
assert [r['word'] for r in rows if r['reading'] == 'しか'] == ['シカ']
assert [r['word'] for r in rows if r['reading'] in ('なす', 'なすび')] == ['ナス']

# Restore the entire previous CSV, so unrelated changes cannot hide in this batch.
heads = blob.decode().splitlines()[0].split(',')
before = {old: dict(row) for old, row in origin.items()}
for change in ledger['changes']:
    if change['action'] == 'edit':
        assert {k for k in heads if change['before'][k] != change['after'][k]} == {'meaning'}
    before[change['beforeId']] = change['before']
restored = io.StringIO()
writer = csv.DictWriter(restored, fieldnames=heads, lineterminator='\n')
writer.writeheader()
writer.writerows(before[i] for i in range(1, ledger['sourceRows']+1))
assert digest(restored.getvalue().encode()) == ledger['beforeSha256']

request = (ROOT / plan['request']).read_text()
ordered = re.findall(r'^## 画像の修正: assets/shiritori/(\S+)', request, re.M)
assert len(ordered) == 55
assert set(ledger['imageEdits']) == set(ordered) - {'wave2-f-word-5640.png'}
manifest = read('assets/shiritori/manifest.json')
assets = {a['file']: a for a in manifest['assets']}
assert len(assets) == len(manifest['assets']) == 1992
catalog = read('data/image-coverage/review-updates.json')
assert digest(blob) == catalog['csvSha256']
assert len(catalog['entries']) == len(rows)
for file, edit in ledger['imageEdits'].items():
    a = assets[file]
    picture_path = ROOT / 'assets/shiritori' / file
    with Image.open(picture_path) as image:
        assert image.size == (256, 256)
        image.verify()
    assert a['sourceSheet'] == edit['sourceSheet'] and a['cropBox'] == edit['cropBox']
    assert a['prompt'] and a['review'].startswith('目視確認済み:')
    assert a['sha256'] == catalog['images']['assets/shiritori/'+file]['sha256'] == digest(picture_path.read_bytes())
for a in assets.values():
    expected = [{'id': i, **{k:r[k] for k in ('reading','word','meaning')}} for i,r in enumerate(rows,1) if r['image_asset'] == 'assets/shiritori/'+a['file']]
    assert expected == [{k:v[k] for k in ('id','reading','word','meaning')} for v in a['aliases']]
    assert any(all(r[k] == a[k] for k in ('reading','word','meaning')) for r in expected)
coverage = read('data/image-coverage/review-2026-10-10.json')
assert len(coverage) == len(rows)
for row, entry in zip(rows, coverage):
    assert all(row[k] == entry[k] for k in ('reading','word','meaning','level','image_asset'))
    if 'wordImage75Review' in entry:
        assert entry['wordImage75Review']['wordReading'] == '未確認'
print(json.dumps({'passed': True, 'orders': 75, 'meaningEdits': 18, 'merges': 3, 'imageEdits': 54, 'rows': len(rows)}, ensure_ascii=False))
