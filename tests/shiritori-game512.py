"""Check stable dictionary lineage, exact senses, grades and alias spelling."""
import csv,json,hashlib,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-27-game512'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'))
raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
assert s['registered'] and len(items)==512 and len(rows)==s['baselineRows']+512
assert hashlib.sha256(raw).hexdigest()==s['afterSha256']
baseline=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n'
assert hashlib.sha256(baseline).hexdigest()==s['beforeSha256'],'All preceding rows byte-preserved'
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json')
updates=read(ROOT/'data/image-coverage/review-updates.json')
grades=read(ROOT/'data/shiritori-grade-review.json')
assert len(coverage)==len(updates['entries'])==len(grades)==len(rows)
assert len({(x['reading'],x['word'],x['meaning']) for x in items})==512
for x in items:
 r=rows[x['id']-1]
 assert all(str(x[k])==r[k] for k in r)
 assert r['image_mode']=='none' and not r['image_asset']
 assert grades[x['id']-1]['level']==5 and grades[x['id']-1]['meaning']==x['meaning']
 assert coverage[x['id']-1]['status']=='explanation-only'
 assert updates['entries'][x['id']-1]['text']==[x['reading'],x['word'],x['meaning']]
 assert x['lexicalSource'] and x['meaningReason'] and x['ageReason']
 if any(y['reading']==x['reading'] for y in rows[:s['baselineRows']]):assert x.get('distinctSenseReason')
for name in ['イオ','ドルマ','ファイア','サンダー','フレア','フリーズ']:
 x=next(x for x in items if x['word']==name)
 assert len([r for r in rows if r['reading']==x['reading']])>=2
 assert 'ドラゴンクエスト' in x['meaning'] or 'ファイナルファンタジー' in x['meaning']
assert next(x for x in items if x['word']=='ホイミ')['meaning'].endswith('少し回復する。')
assert next(x for x in items if x['word']=='ケアル')['meaning'].endswith('体力を回復する。')
assert next(x for x in items if x['word']=='FF7')['reading']=='えふえふせぶん'
assert next(x for x in items if x['word']=='マリメ')['meaning'].startswith('『スーパーマリオメーカー』')
print(json.dumps(dict(passed=True,added=512,rows=len(rows),baselineBytePreserved=True,categories=dict(collections.Counter(x['category'] for x in items))),ensure_ascii=False))
