"""Validate all sheets, prepare R2 transfer, then register the reviewed batch."""
import argparse,collections,csv,hashlib,importlib.util,json,mimetypes,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-culture512'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
run=lambda *a:subprocess.run(a,cwd=ROOT,check=True)
p=argparse.ArgumentParser();p.add_argument('--import-reviewed',action='store_true');args=p.parse_args()
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items']
assert sha((ROOT/'whitelist.csv').read_bytes())==plan['baselineSha256'],'Dictionary changed; rebase IDs before importing'
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
reviews=json.loads((OUT/'semantic-review.json').read_text(encoding='utf-8'))
assert {r['sheet'] for r in reviews if r['passed']}==set(range(1,31))
versions=json.loads((OUT/'sheet-versions.json').read_text(encoding='utf-8')) if (OUT/'sheet-versions.json').exists() else {}
for n in range(1,31):
 suffix=('-'+versions[str(n)]) if str(n) in versions else ''
 source=ROOT/'assets/shiritori/sheets'/f'culture512-sheet{n:02}{suffix}.png';report=OUT/f'sheet{n:02}{suffix}-crop.json'
 grid.verify_report(report,source,ROOT/'assets/shiritori')
 originals=[x for x in items if x['sheet']==n and not x.get('aliasOf')]
 assert next(r for r in reviews if r['sheet']==n)['approvedSlots']==[x['tileIndex'] for x in originals]
 for x in [x for x in items if x['sheet']==n]:
  if suffix:x['filename']=x['filename'].replace('culture512-','culture512'+versions[str(n)]+'-')
  x.update(sourceSheet=source.relative_to(ROOT/'assets/shiritori').as_posix(),cropValidation=report.relative_to(ROOT).as_posix(),prompt=source.with_suffix('.prompt.txt').read_text(encoding='utf-8'))
paths={ROOT/'assets/shiritori'/x['filename'] for x in items}
assert len(paths)==480
paths.update((ROOT/'assets/shiritori/sheets').glob('culture512-*.png'))
paths.update((OUT/'superseded').glob('*.png'))
entries=[dict(key=f.relative_to(ROOT).as_posix(),bucket='shiritori-images' if f.parent==ROOT/'assets/shiritori' else 'shiritori-image-archive',bytes=f.stat().st_size,sha256=sha(f.read_bytes()),contentType=mimetypes.guess_type(f.name)[0]) for f in sorted(paths)]
private=[e for e in entries if e['bucket']=='shiritori-image-archive']
save(OUT/'local-archive-inventory.json',dict(batch=plan['batch'],storage='local-only',entries=private))
entries=[e for e in entries if e['bucket']=='shiritori-images']
save(OUT/'r2-upload.json',dict(batch=plan['batch'],entries=entries))
if not args.import_reviewed:
 print(json.dumps(dict(prepared=True,publicImages=480,objects=len(entries))));sys.exit()
journal=ROOT/'qa-output/culture512-r2-transfer.jsonl'
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')}
assert all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in entries),'R2 upload and readback required'
decisions_path=ROOT/'data/shiritori-grade-decisions.json';decisions=json.loads(decisions_path.read_text(encoding='utf-8'))
assert decisions['sourceSha256']==plan['baselineSha256']
batch=ROOT/'data/dictionary-imports'/(plan['batch']+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow('reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(','))
 for x in items:
  alias=bool(x.get('aliasOf'));w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','assets/shiritori/'+x['filename'] if alias else '','asset' if alias else '',x['credit'] if alias else ''])
save(batch.with_suffix('.review.json'),items)
columns='id,reading,word,meaning,filename,scene,sourceSheet,tileIndex,generatedAt,prompt,cropValidation,credit'.split(',')
imagebatch=ROOT/'data/batches'/(plan['batch']+'-images.csv')
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in items:
  if not x.get('aliasOf'):w.writerow({k:'2026-10-19' if k=='generatedAt' else x[k] for k in columns})
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
run(sys.executable,'-B','-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
manifestpath=ROOT/'assets/shiritori/manifest.json';manifest=json.loads(manifestpath.read_text(encoding='utf-8'))
for x in items:
 if not x.get('aliasOf'):continue
 asset=next(a for a in manifest['assets'] if a['file']==x['filename'])
 assert asset['aliases'][0]['id']==x['sharedWithId']
 asset['aliases'].append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason='同じ芸術家の短い名前と正式名。本人の仕事を説明する同じ画像を共有。',sourceReview=x['imageReason']))
save(manifestpath,manifest)
after=(ROOT/'whitelist.csv').read_bytes();base=(OUT/'registration-baseline.csv').read_bytes();assert after.startswith(base)
rows=list(csv.DictReader(after.decode('utf-8').splitlines()))
assert len(rows)==plan['baselineRows']+512
for level in range(1,6):
 ids=[x['id']-1 for x in items if x['grade']==level]
 if ids:decisions['levels'][str(level)]+=' '+' '.join(map(str,ids))
for x in items:decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
decisions.update(sourceSha256=sha(after),reviewedRows=len(rows));save(decisions_path,decisions)
run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=json.loads(coveragepath.read_text(encoding='utf-8'));assert len(coverage)==plan['baselineRows']
for x in items:
 r=rows[x['id']-1]
 assert r['image_asset']=='assets/shiritori/'+x['filename']
 coverage.append(dict(id=x['id'],**{k:r[k] for k in ('reading','word','meaning','level','image_asset')},category=x['category'],target=True,scopeReason='物語・酒・武器兵器・文化芸術の指定分野追加。',status='covered',assignment='reused' if x.get('aliasOf') else 'new',originalId=None))
save(coveragepath,coverage);save(OUT/'plan.json',plan)
summary=dict(date='2026-10-19',addedMeanings=512,newReadings=512,rows=len(rows),generatedIllustrations=480,sharedNameImages=32,sourceSheets=30,missingImages=0,r2VerifiedObjects=len(entries),beforeSha256=sha(base),afterSha256=sha(after),categories=dict(collections.Counter(x['category'] for x in items)),grades=dict(collections.Counter(x['grade'] for x in items)))
save(OUT/'summary.json',summary);save(batch.with_suffix('.summary.json'),summary)
run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
