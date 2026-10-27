"""Batch-specific checks of stable IDs, shared senses, hashes and R2 evidence."""
import csv,json,hashlib,collections,re
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-27-play1024';E=ROOT/'data/image-coverage/2026-10-27-play1024'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));n=len(items)
raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
assert n>=1024 and s['registered'] and len(rows)==s['baselineRows']+n and hashlib.sha256(raw).hexdigest()==s['afterSha256']
baseline=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n';assert hashlib.sha256(baseline).hexdigest()==s['beforeSha256']
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json');grades=read(ROOT/'data/shiritori-grade-review.json')
manifest=read(ROOT/'assets/shiritori/manifest.json');assets={x['file']:x for x in manifest['assets']};assert len(assets)==len(manifest['assets'])
assert len(coverage)==len(updates['entries'])==len(grades)==len(rows)
assert len({(x['reading'],x['word'],x['meaning']) for x in items})==n
byword={x['word']:x for x in items};groups=collections.defaultdict(list)
for x in items:
 r=rows[x['id']-1];assert all(str(x[k])==r[k] for k in r),(x['word'],r)
 assert re.fullmatch('[ぁ-ゖー]+',x['reading'])
 assert x['lexicalSource'] and x['meaningReason'] and x['ageReason'] and x['imageReason']
 assert grades[x['id']-1]['level']==x['grade'] and grades[x['id']-1]['meaning']==x['meaning']
 assert coverage[x['id']-1]['image_asset']==x['image_asset'] and coverage[x['id']-1]['status']=='covered'
 assert updates['entries'][x['id']-1]['text']==[x['reading'],x['word'],x['meaning']]
 assert any(a['id']==x['id'] and a['meaning']==x['meaning'] for a in assets[Path(x['image_asset']).name]['aliases'])
 if any(y['reading']==x['reading'] for y in rows[:s['baselineRows']]):assert x.get('distinctSenseReason')
 groups[x['canonical']].append(x)
 if x.get('existingCanonicalId'):
  parent=rows[x['existingCanonicalId']-1]
  assert parent['meaning']==x['meaning'] and parent['image_asset']==x['image_asset']
for g in groups.values():assert len({(x['image_asset'],x['meaning']) for x in g})==1
for a in read(E/'manifest-additions.json'):
 p=ROOT/'assets/shiritori'/a['file'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==a['sha256']
 assert updates['images']['assets/shiritori/'+a['file']]['sha256']==a['sha256']
 with Image.open(p) as im:assert im.size==(256,256);im.verify()
assert read(E/'r2-readback.json')['verified']==s['newImages']
for name in ['氷鬼','七並べ','ババ抜き','ポーカー','ウノ','人生ゲーム','モノポリー','カタン','マジック：ザ・ギャザリング','遊戯王カード','デュエマ','オシリスの天空竜','ブラック・マジシャン','ブラック・ロータス']:assert name in byword,name
for a,b in [('MTG','マジック：ザ・ギャザリング'),('デュエマ','デュエル・マスターズ'),('ブラマジ','ブラック・マジシャン'),('ゴレンジャー','秘密戦隊ゴレンジャー')]:
 assert byword[a]['meaning']==byword[b]['meaning'] and byword[a]['image_asset']==byword[b]['image_asset']
assert byword['スピード']['meaning'] not in [x['meaning'] for x in rows[:s['baselineRows']] if x['reading']=='すぴーど']
assert s['newReadings']==len({x['reading'] for x in items}-{r['reading'] for r in rows[:s['baselineRows']]})
print(json.dumps(dict(passed=True,added=n,newReadings=s['newReadings'],aliases=s['sharedAliasRows'],newImages=s['newImages'],reusedExistingImages=s['reusedExistingImages'],oldRowsBytePreserved=True,rows=len(rows)),ensure_ascii=False))
