"""Prepare all reviewed existing-word images, then register after R2 readback."""
import argparse,csv,hashlib,importlib.util,json,mimetypes,shutil,subprocess,sys
from pathlib import Path
R=Path('C:/Users/user/hiragana-ninshiki');O=R/'data/image-coverage/2026-10-25-seven512-images'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
run=lambda *a:subprocess.run(a,cwd=R,check=True)
parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
plan=read(O/'plan.json');items=plan['items'];assert len(items)==512 and len({x['id'] for x in items})==512
reviews={x['sheet']:x for x in read(O/'semantic-review.json') if x['passed']}
assert set(reviews)==set(range(1,33)),f'Missing semantic approvals: {set(range(1,33))-set(reviews)}'
base=(R/'whitelist.csv').read_bytes();assert sha(base)==plan['baselineSha256'],'Dictionary changed: rebase against latest exact senses'
rows=list(csv.DictReader(base.decode('utf-8-sig').splitlines()))
spec=importlib.util.spec_from_file_location('grid',R/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for n,a in reviews.items():
 stage=read(O/f"sheet{n:02}-{a['version']}-staged.json");assert stage['mechanicalPassed']
 source=R/'assets/shiritori'/stage['sourceSheet'];report=R/stage['cropValidation'];staging=R/stage['staging']
 assert sha(source.read_bytes())==a['sourceSha256']==stage['sourceSha256']
 group=[x for x in items if x['sheet']==n];assert a['approvedSlots']==[x['slot'] for x in group]
 grid.verify_report(report,source,staging)
 prompt=source.with_suffix('.prompt.txt').read_text(encoding='utf-8');assert prompt.strip()
 for x in group:
  row=rows[x['id']-1];assert all(row[k]==x[k] for k in ['reading','word','meaning']);assert not row['image_asset']
  src=staging/x['filename'];dest=R/'assets/shiritori'/x['filename']
  if dest.exists():assert dest.read_bytes()==src.read_bytes()
  else:shutil.copy2(src,dest)
  x.update(sourceSheet=stage['sourceSheet'],cropValidation=stage['cropValidation'],prompt=prompt,scene=x['word']+'：'+x['meaning'],image_asset='assets/shiritori/'+x['filename'],image_mode='asset',image_credit='AI生成イラスト')
 grid.verify_report(report,source,R/'assets/shiritori')
if args.prepare:
 (O/'registration-baseline.csv').write_bytes(base)
 manifest=read(R/'assets/shiritori/manifest.json');decisions=read(R/'data/shiritori-grade-decisions.json')
 save(O/'baseline-state.json',dict(manifestAssets=len(manifest['assets']),manifestPrefixSha256=sha(json.dumps(manifest['assets'],ensure_ascii=False,sort_keys=True).encode()),gradeLevelsSha256=sha(json.dumps(decisions['levels'],sort_keys=True).encode())))
 paths={R/'assets/shiritori'/x['filename'] for x in items};paths.update((R/'assets/shiritori/sheets').glob('seven512-sheet*.png'))
 entries=[dict(key=p.relative_to(R).as_posix(),bucket='shiritori-images' if p.parent==R/'assets/shiritori' else 'shiritori-image-archive',bytes=p.stat().st_size,sha256=sha(p.read_bytes()),contentType=mimetypes.guess_type(p.name)[0]) for p in sorted(paths)]
 assert sum(x['bucket']=='shiritori-images' for x in entries)==512
 save(O/'r2-upload.json',dict(batch=plan['batch'],entries=entries))
 cols='id reading word meaning filename scene sourceSheet tileIndex generatedAt prompt cropValidation credit'.split();batch=R/'data/batches/2026-10-25-seven512-images.csv'
 with batch.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader()
  for x in items:w.writerow({k:'2026-10-25' if k=='generatedAt' else 'AI生成イラスト' if k=='credit' else x[k] for k in cols})
 plan.update(status='images-prepared');save(O/'plan.json',plan)
 print(json.dumps(dict(prepared=512,objects=len(entries),bytes=sum(x['bytes'] for x in entries))));sys.exit()
entries=read(O/'r2-upload.json')['entries'];journal=R/'qa-output/seven512-images-r2-transfer.jsonl'
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')}
assert all(verified.get(x['bucket']+'/'+x['key'])==x['sha256'] for x in entries),'Every R2 object must pass server readback'
delivery=read(O/'r2-validation.json');assert delivery['complete'] and delivery['publicDownloadedAndSha256Matched']==512
decisions=read(R/'data/shiritori-grade-decisions.json');assert decisions['sourceSha256']==sha(base)
run(sys.executable,'-B','-X','utf8','scripts/import-shiritori-assets.py','data/batches/2026-10-25-seven512-images.csv')
after=(R/'whitelist.csv').read_bytes();current=list(csv.DictReader(after.decode('utf-8').splitlines()));assert len(current)==len(rows)
baseline_state=read(O/'baseline-state.json');manifest=read(R/'assets/shiritori/manifest.json')
assert len(manifest['assets'])==baseline_state['manifestAssets']+512
assert sha(json.dumps(manifest['assets'][:baseline_state['manifestAssets']],ensure_ascii=False,sort_keys=True).encode())==baseline_state['manifestPrefixSha256']
target={x['id'] for x in items}
for i,(old,new) in enumerate(zip(rows,current),1):
 for k in old:
  if i not in target or k not in ['image_asset','image_mode','image_credit']:assert old[k]==new[k],(i,k)
decisions['sourceSha256']=sha(after);save(R/'data/shiritori-grade-decisions.json',decisions)
coverage=read(R/'data/image-coverage/review-2026-10-10.json');assert len(coverage)==len(rows)
for x in items:
 c=coverage[x['id']-1];assert all(c[k]==x[k] for k in ['reading','word','meaning'])
 c.update(image_asset=x['image_asset'],status='covered',assignment='new',target=True,imageBatch=plan['batch'])
save(R/'data/image-coverage/review-2026-10-10.json',coverage)
run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-review-updates.py')
inventory=read(R/'data/image-coverage/r2-assets.json');index={x['key']:x for x in inventory['entries']};index.update({x['key']:x for x in entries});inventory['entries']=sorted(index.values(),key=lambda x:x['key']);inventory['dictionaryImageReferences']=len({x['image_asset'] for x in current if x['image_asset']});inventory['revision']=sha(json.dumps(inventory['entries'],sort_keys=True).encode());save(R/'data/image-coverage/r2-assets.json',inventory)
summary=dict(registeredImages=512,newVocabularyRows=0,totalRows=len(current),sourceSheets=32,categoryCounts=plan['categoryCounts'],beforeSha256=sha(base),afterSha256=sha(after),missingImages=0,publicReadbackSha256Matched=512,objectsVerified=len(entries),copyrightedCharactersUsed=False,browserValidation='pending')
save(O/'summary.json',summary);plan.update(status='registered',summary=summary);save(O/'plan.json',plan);save(O/'checkpoint.json',dict(planned=512,generated=512,mechanicallyValidated=512,semanticallyApproved=512,registered=512,pending=0))
print(json.dumps(summary,ensure_ascii=False))
