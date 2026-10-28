"""Verify provenance, exact registration, difficulty and append-only preservation."""
import csv,json,hashlib,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-28-art-history'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.final-review.json'));source=read(BASE.with_suffix('.sources.json'));raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf8').splitlines()))
n=len(items);assert s['registered'] and n>2000
before=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n';after=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+n+1])+b'\n'
assert hashlib.sha256(before).hexdigest()==s['beforeSha256']
originalBatch=BASE.with_suffix('.csv').read_bytes().split(b'\n',1)[1]
assert hashlib.sha256(before+originalBatch).hexdigest()==s['afterSha256']
corrections=read(BASE.with_suffix('.corrections.json'));assert all(x['beforeId']>s['baselineRows'] for x in corrections)
grades=read(ROOT/'data/shiritori-grade-review.json');coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json')
assert len(rows)==len(grades)==len(coverage)==len(updates['entries'])
assert updates['csvSha256']==hashlib.sha256(raw).hexdigest()
assert len({(x['reading'],x['word'],x['meaning']) for x in items})==n
for x in items:
 assert all(rows[x['id']-1][k]==x[k] for k in rows[0])
 assert re.fullmatch('[ぁ-ゖー]+',x['reading'])
 assert x['image_mode']=='none' and not x['image_asset'] and not x['imagequery']
 assert x['revision'] and x['sourceUrl'].endswith(str(x['revision']))
 assert x['readingSource']!='機械読み候補（要確認）' or not re.search('[一-龥々]',x['word'])
 assert grades[x['id']-1]['level']==5 and grades[x['id']-1]['meaning']==x['meaning']
 assert coverage[x['id']-1]['status']=='explanation-only'
 assert updates['entries'][x['id']-1]['text']==[x['reading'],x['word'],x['meaning']]
required={'星月夜':'ほしづきよ','印象派':'いんしょうは','スフマート':'すふまーと','神奈川沖浪裏':'かながわおきなみうら','松林図屏風':'しょうりんずびょうぶ'}
for w,r in required.items():assert any(x['word']==w and x['reading']==r for x in items),w
supp=read(ROOT/'data/dictionary-imports/2026-10-28-art-history-supplement.summary.json')
completion=read(ROOT/'data/dictionary-imports/2026-10-28-art-history-completion.summary.json')
assert collections.Counter(s['categories'])+collections.Counter(supp['categories'])+collections.Counter(completion['categories'])==collections.Counter(x['category'] for x in items)
assert n==s['added']+supp['added']+completion['added']
print(json.dumps(dict(passed=True,added=n,total=len(rows),baselineBytePreserved=True,categories=dict(collections.Counter(x['category'] for x in items))),ensure_ascii=False))
