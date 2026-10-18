"""Persist resumable 512-word groups without changing the live dictionary."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/image-coverage/2026-10-18-expansion1024h'
plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
reviews = {r['sourceSheet']: r for r in json.loads((OUT / 'semantic-review.json').read_text(encoding='utf-8')) if r['passed']}
stages = {}
for path in sorted(OUT.glob('sheet*-staged.json')):
    entry = json.loads(path.read_text(encoding='utf-8'))
    stages.setdefault(entry['sheet'], []).append(entry)
groups = []
for first, last in [(1, 32), (33, 64)]:
    sheets = []
    for n in range(first, last + 1):
        versions = stages.get(n, [])
        ready = [s for s in versions if s['passed'] and s['sourceSheet'] in reviews]
        selected = ready[-1] if ready else None
        sheets.append(dict(sheet=n, generated=bool(versions), cropPassed=any(s['passed'] for s in versions),
                           ready=bool(selected), selectedSource=selected['sourceSheet'] if selected else None))
    groups.append(dict(firstSheet=first, lastSheet=last, plannedWords=512,
                       readyWords=16 * sum(s['ready'] for s in sheets), sheets=sheets))
result = dict(batch='2026-10-18-expansion1024h', groupSize=512,
              baselineUnchanged=hashlib.sha256((ROOT / 'whitelist.csv').read_bytes()).hexdigest() == plan['baselineSha256'],
              groups=groups)
(OUT / 'checkpoint.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(baselineUnchanged=result['baselineUnchanged'], groups=[dict(firstSheet=g['firstSheet'],lastSheet=g['lastSheet'],readyWords=g['readyWords'],missingSheets=[s['sheet'] for s in g['sheets'] if not s['generated']],pendingSheets=[s['sheet'] for s in g['sheets'] if not s['ready']]) for g in groups]),ensure_ascii=False))
