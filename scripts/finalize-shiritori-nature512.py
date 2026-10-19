"""Prepare verified crops/R2 inventory, then atomically import reviewed meanings."""
import argparse,collections,csv,hashlib,importlib.util,json,mimetypes,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def run(*a):subprocess.run(a,cwd=R,check=True)
ap=argparse.ArgumentParser();ap.add_argument('--import-reviewed',action='store_true');ap.add_argument('--local-first',action='store_true',help='Reserve verified local rows before transfer during simultaneous dictionary additions');args=ap.parse_args()
p=read(O/'plan.json');items=p['items'];N=len(items);S=len(p['sheets']);base=(R/'whitelist.csv').read_bytes()
rows=list(csv.DictReader(base.decode('utf-8').splitlines()));fields=list(rows[0]);oldcount=len(rows)
if not args.import_reviewed:
 assert not p.get('registered'),'Already registered'
 existing_readings={x['reading'] for x in rows}
 assert all(x.get('distinctSenseReason') for x in items if x['reading'] in existing_readings),'Rebase overlapping words first'
 semantic=read(O/'semantic-review.json');assert len(semantic)==S and all(x['passed'] for x in semantic)
 spec=importlib.util.spec_from_file_location('grid',R/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
 for offset,x in enumerate(items):x.update(id=oldcount+offset+1,filename=f'nature512-b{oldcount}-word-{oldcount+offset+1}.png',credit='AI生成イラスト')
 for n in range(1,S+1):
  staged=read(O/f'sheet{n:02}-staged.json');source=R/staged['source'];approved=next(x for x in semantic if x['sheet']==n)
  assert staged['sha256']==sha(source.read_bytes())==approved['sha256']
  tiles=[x for x in items if x['sheet']==n];report=O/f'final-{oldcount}-sheet{n:02}-crop.json'
  cmd=[sys.executable,'-B','-X','utf8','scripts/crop-shiritori-grid.py',str(source),'--method','magenta-grid-lines-only-v4','--names',','.join(Path(x['filename']).stem for x in tiles),'--output',str(R/'assets/shiritori'),'--report',str(report)]
  if report.exists():cmd.append('--verify-existing')
  run(*cmd);grid.verify_report(report,source,R/'assets/shiritori')
  for x in tiles:x.update(sourceSheet=source.relative_to(R/'assets/shiritori').as_posix(),cropValidation=report.relative_to(R).as_posix(),prompt=source.with_suffix('.prompt.txt').read_text(encoding='utf-8'))
 paths={R/'assets/shiritori'/x['filename'] for x in items};paths.update((R/'assets/shiritori/sheets').glob('nature512-*.png'))
 entries=[dict(key=f.relative_to(R).as_posix(),bucket='shiritori-images' if f.parent==R/'assets/shiritori' else 'shiritori-image-archive',bytes=f.stat().st_size,sha256=sha(f.read_bytes()),contentType=mimetypes.guess_type(f.name)[0]) for f in sorted(paths)]
 save(O/'r2-upload.json',dict(batch=p['batch'],entries=entries));(O/'import-baseline.csv').write_bytes(base)
 for s in p['sheets']:s['tiles']=[x for x in items if x['sheet']==s['sheet']]
 p.update(importBaselineRows=oldcount,importBaselineSha256=sha(base),status='images-prepared');save(O/'plan.json',p)
 print(json.dumps(dict(prepared=True,publicImages=N,objects=len(entries),baselineRows=oldcount)));sys.exit()
assert sha(base)==p['importBaselineSha256'],'Dictionary changed since image preparation; rerun preparation against latest IDs'
entries=read(O/'r2-upload.json')['entries'];journal=R/'qa-output/nature512-r2-transfer.jsonl'
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')} if journal.exists() else {}
if not args.local_first:
 assert all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in entries),'Every R2 object needs matching transfer verification'
 delivery=read(O/'r2-validation.json');assert delivery['complete'] and delivery['publicDownloadedAndSha256Matched']==N
decision_path=R/'data/shiritori-grade-decisions.json';decisions=read(decision_path);assert decisions['sourceSha256']==sha(base)
batch=R/'data/dictionary-imports'/f'{p["batch"]}.csv'
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
 for x in items:w.writerow(dict(reading=x['reading'],word=x['word'],meaning=x['meaning'],imagequery=x['word'],level=x['level'],imagequery_en=x.get('scientificName') or x.get('english',''),image_asset='',image_mode='',image_credit=''))
save(batch.with_suffix('.review.json'),items)
imagebatch=R/'data/batches'/f'{p["batch"]}-images.csv';cols='id reading word meaning filename scene sourceSheet tileIndex generatedAt prompt cropValidation credit'.split()
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader()
 for x in items:w.writerow({k:'2026-10-19' if k=='generatedAt' else x[k] for k in cols})
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
run(sys.executable,'-B','-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
imagebytes=(R/'whitelist.csv').read_bytes();assert imagebytes.startswith(base)
current=list(csv.DictReader(imagebytes.decode('utf-8').splitlines()))
assert len(current)==oldcount+N
# Enrich the already-present element sense, never add a second entry for it.
corrections=[];element_registry=[]
for e in read(O/'elements.json'):
 matches=[(i,r) for i,r in enumerate(current,1) if r['reading']==e['reading'] and r['word']==e['word']]
 if any(i>oldcount for i,r in matches):matches=[(i,r) for i,r in matches if i>oldcount]
 assert len(matches)==1,(e['word'],matches)
 ident,r=matches[0]
 if ident<=oldcount and r['meaning']!=e['meaning']:
  before=dict(r);r['meaning']=f'原子番号{e["atomicNumber"]}、元素記号{e["symbol"]}の元素。'+r['meaning'];corrections.append(dict(action='edit',beforeId=ident,before=before,after=dict(r)))
 element_registry.append(dict(id=ident,**{k:e[k] for k in ['reading','word','atomicNumber','symbol','english']},image_asset=r['image_asset']))
if corrections:
 with (R/'whitelist.csv').open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(current)
 hpath=R/'data/dictionary-imports/history.json';history=read(hpath);assert history[-1]['afterSha256']==sha(imagebytes)
 after=(R/'whitelist.csv').read_bytes()
 history.append(dict(type='reviewed-corrections',batch=f'data/image-coverage/{p["batch"]}/existing-elements.json',sourceRows=len(current),currentRows=len(current),currentBeforeIds=list(range(1,len(current)+1)),beforeSha256=sha(imagebytes),afterSha256=sha(after),changes=corrections));save(hpath,history)
 manifestpath=R/'assets/shiritori/manifest.json';manifest=read(manifestpath)
 changed={c['beforeId']:c for c in corrections}
 for asset in manifest['assets']:
  for alias in asset.get('aliases',[]):
   if alias['id'] in changed:alias['meaning']=current[alias['id']-1]['meaning']
  if asset.get('aliases') and asset['aliases'][0]['id'] in changed:asset['meaning']=asset['aliases'][0]['meaning']
 save(manifestpath,manifest)
save(O/'existing-elements.json',corrections);save(O/'element-registry.json',element_registry)
after=(R/'whitelist.csv').read_bytes()
for x in items:
 r=current[x['id']-1];assert r['image_asset']=='assets/shiritori/'+x['filename']
 for k in ['image_asset','image_mode','image_credit']:x[k]=r[k]
for level in range(1,6):
 indices=[str(x['id']-1) for x in items if x['grade']==level]
 if indices:decisions['levels'][str(level)]+=' '+' '.join(indices)
for x in items:decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
decisions.update(sourceSha256=sha(after),reviewedRows=len(current));save(decision_path,decisions)
coveragepath=R/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragepath);assert len(coverage)==oldcount
for c in corrections:coverage[c['beforeId']-1]['meaning']=c['after']['meaning']
for x in items:
 r=current[x['id']-1];coverage.append(dict(id=x['id'],**{k:r[k] for k in ['reading','word','meaning','level','image_asset']},category=x['category'],target=True,scopeReason='元素・天使悪魔・装飾品・宝石鉱物・生物の指定分野追加。',status='covered',assignment='new',originalId=None))
save(coveragepath,coverage);save(batch.with_suffix('.review.json'),items)
run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-review-updates.py')
summary=dict(date='2026-10-19',addedMeanings=N,newReadings=len({x['reading'] for x in items}-{r['reading'] for r in rows}),generatedIllustrations=N,sourceSheets=S,enrichedExistingElements=len(corrections),elementsCovered=len(element_registry),rows=len(current),missingImages=0,r2ExpectedObjects=len(entries),r2VerifiedObjects=sum(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in entries),r2TransferPending=args.local_first,beforeSha256=sha(base),afterSha256=sha(after),categories=dict(collections.Counter(x['category'] for x in items)),grades=dict(collections.Counter(x['grade'] for x in items)))
p.update(registered=summary,status='registered');save(O/'plan.json',p);save(O/'summary.json',summary);save(batch.with_suffix('.summary.json'),summary)
# Merge only this batch into the delivery inventory; preserve other simultaneous batches.
inventorypath=R/'data/image-coverage/r2-assets.json';inventory=read(inventorypath);index={e['key']:e for e in inventory['entries']}
index.update({e['key']:e for e in entries});inventory['entries']=sorted(index.values(),key=lambda x:x['key']);inventory['dictionaryImageReferences']=len({r['image_asset'] for r in current if r['image_asset']});inventory['revision']=sha(json.dumps(inventory['entries'],sort_keys=True).encode());save(inventorypath,inventory)
print(json.dumps(summary,ensure_ascii=False))
