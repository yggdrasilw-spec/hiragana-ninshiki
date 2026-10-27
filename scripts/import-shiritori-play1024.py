"""Commit a completely staged and remotely verified vocabulary batch locally."""
import csv,json,hashlib,subprocess,sys,shutil,collections
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-27-play1024'
EVIDENCE=ROOT/'data/image-coverage/2026-10-27-play1024'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));n=len(items)
 assert n>=1024 and s['added']==n
 if s['registered']:print(json.dumps(dict(alreadyRegistered=True,added=n)));return
 raw=(ROOT/'whitelist.csv').read_bytes();assert sha(raw)==s['beforeSha256'],'Concurrent dictionary edit; rebase first'
 old=list(csv.DictReader(raw.decode('utf-8').splitlines()));assert len(old)==s['baselineRows']
 manifest=read(ROOT/'assets/shiritori/manifest.json');byfile={a['file']:a for a in manifest['assets']}
 additions=read(EVIDENCE/'manifest-additions.json');reused=read(EVIDENCE/'manifest-reused.json')
 d=read(ROOT/'data/shiritori-grade-decisions.json');coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json')
 assert d['sourceSha256']==updates['csvSha256']==sha(raw)
 assert len(old)==d['reviewedRows']==len(coverage)==len(updates['entries'])
 for a in additions:
  assert a['file'] not in byfile
  b=(ROOT/'assets/shiritori'/a['file']).read_bytes();assert sha(b)==a['sha256']
  byfile[a['file']]=a;manifest['assets'].append(a)
 for record in reused:
  target=byfile[record['file']]
  for x in record['aliases']:
   assert x['meaning']==old[record['canonicalId']-1]['meaning']
   assert not any(a['id']==x['id'] for a in target['aliases'])
   target['aliases'].append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason='登録済みの漫画作品名と略称で同じ説明・画像を共有。',sourceReview='2026-10-27-play1024'))
 for x in items:
  a=byfile[Path(x['image_asset']).name]
  assert any(v['id']==x['id'] and v['word']==x['word'] and v['meaning']==x['meaning'] for v in a['aliases'])
 node=shutil.which('node');assert node
 def run(*args):subprocess.run(args,cwd=ROOT,check=True)
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 if '--import-reviewed' not in sys.argv:return
 journal=ROOT/'qa-output/play1024-r2-transfer.jsonl'
 lines=journal.read_text(encoding='utf-8').splitlines()
 corrections=ROOT/'qa-output/play1024-r2-corrections-transfer.jsonl'
 if corrections.exists():lines+=corrections.read_text(encoding='utf-8').splitlines()
 verified={v['key']:v for line in lines if (v:=json.loads(line)).get('verified')}
 inventory=read(EVIDENCE/'r2-inventory.json')
 assert all(e['key'] in verified and verified[e['key']]['sha256']==e['sha256'] and verified[e['key']]['bytes']==e['bytes'] for e in inventory['entries']),'R2 readback incomplete'
 backup=ROOT/'qa-output/play1024-before';backup.mkdir(exist_ok=True)
 for name in ['whitelist.csv','assets/shiritori/manifest.json','data/dictionary-imports/history.json','data/shiritori-grade-decisions.json','data/image-coverage/review-2026-10-10.json','data/image-coverage/review-updates.json','data/image-coverage/r2-assets.json','data/shiritori-grade-review.json','shiritori-grade-policy.js']:
  p=backup/name;p.parent.mkdir(parents=True,exist_ok=True)
  assert not p.exists(),'Backup already exists; inspect a previous import attempt'
  shutil.copyfile(ROOT/name,p)
 assert (ROOT/'whitelist.csv').read_bytes()==raw
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(ROOT/'whitelist.csv').read_bytes();assert after.startswith(raw) and len(after.splitlines())-1==len(old)+n
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 for x in items:
  d['levels'][str(x['grade'])]+=' '+str(x['id']-1);d.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
  coverage.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],level=str(x['level']),image_asset=x['image_asset'],category=x['category'],target=True,scopeReason='日常の遊び・カードとボードゲーム・作品名と略称の追加。正式名と略称は画像・説明を共有。',status='covered',assignment='reused' if 'aliasOf' in x or x.get('existingCanonicalId') else 'new',originalId=None,imageBatch='2026-10-27-play1024'))
  updates['entries'].append(dict(id=x['id'],text=[x['reading'],x['word'],x['meaning']],textUpdatedAt=now,image_asset=x['image_asset'],imageAssignedAt=now))
 d.update(sourceSha256=sha(after),reviewedRows=len(old)+n);save(ROOT/'data/shiritori-grade-decisions.json',d)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
 save(ROOT/'data/image-coverage/review-2026-10-10.json',coverage);save(ROOT/'assets/shiritori/manifest.json',manifest)
 updates['csvSha256']=sha(after);updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 for a in additions:updates['images']['assets/shiritori/'+a['file']]=dict(sha256=a['sha256'],updatedAt=now)
 updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 (ROOT/'data/image-coverage/review-updates.json').write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 global_inventory=read(ROOT/'data/image-coverage/r2-assets.json');keys={e['key'] for e in global_inventory['entries']}
 assert not keys.intersection(e['key'] for e in inventory['entries'])
 global_inventory['entries']+=inventory['entries'];global_inventory['entries'].sort(key=lambda e:(e['bucket'],e['key']))
 global_inventory['dictionaryImageReferences']=len({x['image_asset'] for x in old+items if x['image_asset']})
 global_inventory['revision']=sha(json.dumps(global_inventory['entries'],sort_keys=True).encode());save(ROOT/'data/image-coverage/r2-assets.json',global_inventory)
 save(EVIDENCE/'r2-readback.json',dict(passed=True,checkedAt=now,verified=len(inventory['entries']),entries=[verified[e['key']] for e in inventory['entries']]))
 s.update(registered=True,afterSha256=sha(after),totalRows=len(old)+n,r2Verified=len(inventory['entries']));save(BASE.with_suffix('.summary.json'),s)
 print(json.dumps(s,ensure_ascii=False))
if __name__=='__main__':main()
