"""Build an immutable, crop-verified R2 transfer list before dictionary import."""
import hashlib
import importlib.util
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/image-coverage/2026-10-18-expansion1024h'
plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT / 'whitelist.csv').read_bytes()).hexdigest() == plan['baselineSha256']
approved = {x['sourceSheet']: x for x in json.loads((OUT / 'semantic-review.json').read_text(encoding='utf-8')) if x['passed']}
selected = {}
for path in sorted(OUT.glob('sheet*-staged.json')):
    stage = json.loads(path.read_text(encoding='utf-8'))
    if stage['passed'] and stage['sourceSheet'] in approved:
        selected[stage['sheet']] = stage
assert set(selected) == set(range(1, 65)), 'All 64 sheets must be ready'
spec = importlib.util.spec_from_file_location('grid', ROOT / 'scripts/crop-shiritori-grid.py')
grid = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grid)
paths = set()
for number, stage in selected.items():
    group = [x for x in plan['items'] if x['sheet'] == number]
    assert approved[stage['sourceSheet']]['approvedSlots'] == [x['slot'] for x in group]
    grid.verify_report(ROOT / stage['cropValidation'], ROOT / 'assets/shiritori' / stage['sourceSheet'], ROOT / 'assets/shiritori')
    paths.update(ROOT / 'assets/shiritori' / x['filename'] for x in group)
# Keep generated originals, rejected versions, and superseded crops private.
paths.update((ROOT / 'assets/shiritori/sheets').glob('expansion1024h-sheet*.png'))
paths.update((OUT / 'superseded').rglob('*.png'))
entries = []
for path in sorted(paths):
    public = path.parent == ROOT / 'assets/shiritori'
    entries.append(dict(key=path.relative_to(ROOT).as_posix(), bucket='shiritori-images' if public else 'shiritori-image-archive', bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), contentType=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'))
assert sum(e['bucket'] == 'shiritori-images' for e in entries) == 1024
result = dict(batch=plan['batch'], entries=entries)
(OUT / 'r2-upload.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(objects=len(entries), public=1024, private=len(entries)-1024, bytes=sum(e['bytes'] for e in entries))))
