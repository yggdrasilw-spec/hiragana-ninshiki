"""Check intake provenance, exact prior bytes and each runtime ledger."""
import csv,json,hashlib,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-28-highschool'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda b:hashlib.sha256(b).hexdigest()
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'))
raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
n=s['added'];b=s['baselineRows'];assert s['registered'] and n==228
assert sha(b'\n'.join(raw.split(b'\n')[:b+1])+b'\n')==s['beforeSha256']
assert sha(b'\n'.join(raw.split(b'\n')[:b+n+1])+b'\n')==s['afterSha256']
assert collections.Counter(x['category'] for x in items)==s['categories']
assert len({(x['reading'],x['word']) for x in items})==n
assert not {x['word'] for x in items}&{x['word'] for x in rows[:b]}
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json')
updates=read(ROOT/'data/image-coverage/review-updates.json')
grades=read(ROOT/'data/shiritori-grade-review.json')
assert len(coverage)==len(updates['entries'])==len(grades)==len(rows)
assert updates['csvSha256']==sha(raw)
for x in items:
 i=x['id']-1;r=rows[i]
 assert all(r[k]==str(x[k]) for k in r)
 assert re.fullmatch('[ぁ-ゖー]+',r['reading']) and r['image_mode']=='none' and not r['image_asset']
 assert grades[i]['level']==5 and grades[i]['meaning']==r['meaning']
 assert coverage[i]['status']=='explanation-only' and coverage[i]['meaning']==r['meaning']
 assert updates['entries'][i]['text']==[r['reading'],r['word'],r['meaning']]
 assert x['lexicalSource']['references'] and x['meaningReason'] and x['ageReason']
 if any(y['reading']==x['reading'] for y in rows[:b]):assert x['distinctSenseReason']
for word,reading in {'をかし':'おかし','あはれ':'あわれ','あはれなり':'あわれなり','らうたし':'ろうたし','やむごとなし':'やんごとなし','参づ':'もうず','已然形':'いぜんけい','疎外':'そがい','四聖諦':'ししょうたい'}.items():
 assert any(x['word']==word and x['reading']==reading for x in items),(word,reading)
print(json.dumps(dict(passed=True,added=n,preservedRows=b,totalRows=len(rows),categories=s['categories'],newReadings=s['newReadings'],endingN=s['endingN']),ensure_ascii=False))
