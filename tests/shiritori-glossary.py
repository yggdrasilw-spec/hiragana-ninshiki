"""Verify the batch against source bytes, prior IDs and runtime catalogs."""
import csv,json,hashlib,re,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-28-glossary'
read=lambda p:json.loads(p.read_text(encoding='utf-8'));sha=lambda b:hashlib.sha256(b).hexdigest()
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));n=s['added'];b=s['baselineRows']
raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
assert s['registered'] and n>=2500
assert sha(b'\n'.join(raw.split(b'\n')[:b+1])+b'\n')==s['beforeSha256'],'Previous rows changed'
assert sha(b'\n'.join(raw.split(b'\n')[:b+n+1])+b'\n')==s['afterSha256'],'Intake prefix changed'
assert len(items)==n and len({(x['reading'],x['word'],x['meaning']) for x in items})==n
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json');grades=read(ROOT/'data/shiritori-grade-review.json')
assert len(coverage)==len(updates['entries'])==len(grades)==len(rows)
assert updates['csvSha256']==sha(raw)
sources=read(BASE.with_suffix('.sources.json'));assert sha((ROOT/sources['ipsj']['file']).read_bytes())==sources['ipsj']['sha256']
sourceRows=list(csv.DictReader((ROOT/sources['ipsj']['file']).open(encoding='utf-8-sig')))
for x in items:
 i=x['id']-1;r=rows[i]
 assert all(r[k]==str(x[k]) for k in r),(x['word'],x['id'])
 assert re.fullmatch('[ぁ-ゖー]+',r['reading']) and r['image_mode']=='none' and not r['image_asset']
 assert grades[i]['level']==5 and grades[i]['meaning']==r['meaning']
 assert coverage[i]['status']=='explanation-only' and coverage[i]['meaning']==r['meaning']
 assert updates['entries'][i]['text']==[r['reading'],r['word'],r['meaning']]
 assert x['lexicalSource']['references'] and x['meaningReason'] and x['ageReason']
 if x['origin']=='ipsj':
  src=sourceRows[x['lexicalSource']['sourceRow']-2];assert x['word'] in [t.strip() for t in src['用語'].split('|')]
  assert x['lexicalSource']['license']=='CC BY-SA 4.0' and x['lexicalSource']['definitionTransform']
for words in [('ミル','ジョン・スチュアート・ミル'),('龍樹','ナーガールジュナ'),('ハンナ・アーレント','ハンナ・アレント'),('ブッダ','釈迦牟尼'),('デジタル','ディジタル')]:
 assert all(any(x['word']==w for x in rows) for w in words),words
for w,r in {'西周':'にしあまね','朱子':'しゅし','五行':'ごこう','西行':'さいぎょう','著作者人格権':'ちょさくしゃじんかくけん','外れ値':'はずれち','あぢきなし':'あじきなし','侍り':'はべり'}.items():
 assert any(x['word']==w and x['reading']==r for x in rows),(w,r)
assert collections.Counter(x['category'].split('／')[0] for x in items)==s['areas']
print(json.dumps(dict(passed=True,added=n,previousRows=b,totalRows=len(rows),areas=s['areas'],variants=True,sourceHash=True),ensure_ascii=False))
