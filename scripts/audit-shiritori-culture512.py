"""Audit the exact new meanings, name aliases, five levels and R2 records."""
import collections,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-culture512'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(OUT/'plan.json');items=plan['items'];current=(ROOT/'whitelist.csv').read_bytes()
snapshot=OUT/'registration-baseline.csv'
base=snapshot.read_bytes() if snapshot.exists() else b''.join(current.splitlines(keepends=True)[:plan['baselineRows']+1])
assert hashlib.sha256(base).hexdigest()==plan['baselineSha256']
rows=list(csv.DictReader(current.decode('utf-8').splitlines()));original=list(csv.DictReader(base.decode('utf-8').splitlines()))
assert current.startswith(base),'Preceding dictionary rows changed'
assert len(items)==512 and len(rows)>=len(original)+512
assert len({x['reading'] for x in items})==512
assert not {x['reading'] for x in items}&{x['reading'] for x in original}
manifest=read(ROOT/'assets/shiritori/manifest.json');assets={x['file']:x for x in manifest['assets']}
grades={x['id']:x for x in read(ROOT/'data/shiritori-grade-review.json')}
coverage={x['id']:x for x in read(ROOT/'data/image-coverage/review-2026-10-10.json')}
inventory=read(OUT/'r2-upload.json');objects={(e['bucket'],e['key']):e for e in inventory['entries']}
alias_count=0
for x in items:
 r=rows[x['id']-1]
 for k in ('reading','word','meaning'):assert r[k]==x[k],(x['id'],k)
 assert grades[x['id']]['level']==x['grade']
 assert x['grade']==5 or x['category']=='tales'
 assert r['image_asset']=='assets/shiritori/'+x['filename'] and r['image_mode']=='asset'
 assert x['lexicalSource'] and x['meaningReason'] and x['ageReason'] and x['imageReason']
 a=assets[x['filename']];assert any(z['id']==x['id'] and z['meaning']==x['meaning'] for z in a['aliases'])
 e=objects['shiritori-images',r['image_asset']]
 assert hashlib.sha256((ROOT/r['image_asset']).read_bytes()).hexdigest()==e['sha256']
 if x.get('aliasOf'):
  alias_count+=1;parent=next(z for z in items if z['reading']==x['aliasOf'])
  assert parent['id']==x['sharedWithId'] and parent['filename']==x['filename'] and parent['grade']==x['grade']
  assert coverage[x['id']]['assignment']=='reused'
 else:assert coverage[x['id']]['assignment']=='new'
assert alias_count==32 and len({x['filename'] for x in items})==480
for short,full in [('もね','くろーどもね'),('ごっほ','ふぃんせんとふぁんごっほ')]:
 a,b=[next(x for x in items if x['reading']==r) for r in (short,full)];assert a['filename']==b['filename']
assert read(ROOT/'data/dictionary-imports/history.json')[-1]['afterSha256']==hashlib.sha256(current).hexdigest()
result=dict(passed=True,meanings=512,newReadings=512,generatedImages=480,nameAliases=32,precedingRowsUnchanged=len(original),categories=dict(collections.Counter(x['category'] for x in items)),grades=dict(collections.Counter(x['grade'] for x in items)))
(OUT/'data-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
