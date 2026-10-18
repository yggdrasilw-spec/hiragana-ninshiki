"""Require all 64 verified sheets and real content reviews before importing 1024 words."""
import collections,csv,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-18-expansion1024h';OUT=ROOT/'data/image-coverage'/NAME
save=lambda p,o:p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
run=lambda *args:subprocess.run(args,cwd=ROOT,check=True)
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items']
assert len(items)==1024 and len({x['reading'] for x in items})==1024
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
approved={x['sourceSheet']:x for x in json.loads((OUT/'semantic-review.json').read_text(encoding='utf-8')) if x['passed']}
selected={}
for p in sorted(OUT.glob('sheet*-staged.json')):
 s=json.loads(p.read_text(encoding='utf-8'))
 if s['passed'] and s['sourceSheet'] in approved:selected[s['sheet']]=s
assert set(selected)==set(range(1,65)),'Every sheet requires measured crops AND a real semantic review'
for n,s in selected.items():
 group=[x for x in items if x['sheet']==n]
 assert approved[s['sourceSheet']]['approvedSlots']==[x['slot'] for x in group]
 grid.verify_report(ROOT/s['cropValidation'],ROOT/'assets/shiritori'/s['sourceSheet'],ROOT/'assets/shiritori')
 for x in group:x.update(sourceSheet=s['sourceSheet'],cropValidation=s['cropValidation'],prompt=s['prompt'],scene=x['word']+'：'+x['meaning'],imageStatus='covered',imageAssignment='new')
base=(OUT/'registration-baseline.csv').read_bytes();assert sha(base)==plan['baselineSha256'];assert (ROOT/'whitelist.csv').read_bytes()==base,'Concurrent dictionary change: rebase instead of overwriting'
# Capture exact old grade decisions before dictionary mutation.
gradepath=ROOT/'data/shiritori-grade-decisions.json';decisions=json.loads(gradepath.read_text(encoding='utf-8'))
assert decisions['sourceSha256']==sha(base) and decisions['reviewedRows']==plan['baselineRows']
# All upload journal entries must contain server-readback checksums before dictionary references go live.
upload=json.loads((OUT/'r2-upload.json').read_text(encoding='utf-8'))
journal=ROOT/'qa-output/expansion1024h-r2-transfer.jsonl'
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')}
assert all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in upload['entries']),'Upload and verify every new image first'
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
batch=ROOT/'data/dictionary-imports'/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(header)
 for x in items:
  assert not any(',' in str(x[k]) or '\n' in str(x[k]) for k in ('reading','word','meaning'))
  w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
save(ROOT/'data/dictionary-imports'/(NAME+'.review.json'),items)
save(ROOT/'data/dictionary-imports'/(NAME+'.source.json'),dict(source='JMdict',dictDate=plan['sourceDate'],sourceSha256=plan['sourceSha256'],attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',licenseUrl='https://www.edrdg.org/edrdg/licence.html',definitions='Japanese explanations independently written for this batch.',rows=[{k:x[k] for k in ('reading','word','entryId','senseIndex','gloss','sources','senseIndices') if k in x} for x in items]))
columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
imagebatch=ROOT/'data/batches'/(NAME+'-images.csv')
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in items:w.writerow({k:'2026-10-18' if k=='generatedAt' else 'AI生成イラスト' if k=='credit' else x[k] for k in columns})
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
after=(ROOT/'whitelist.csv').read_bytes();assert after.startswith(base),'Preserve preceding rows and IDs'
rows=list(csv.DictReader(after.decode('utf-8').splitlines()));assert len(rows)==plan['baselineRows']+1024
for x in items:
 r=rows[x['id']-1];assert all(r[k]==str(x[k]) for k in ('reading','word','meaning','level'));assert r['image_asset']=='assets/shiritori/'+x['filename']
# Rebase existing meaning decisions; append only the new exact meanings.
for level in range(1,6):
 indices=[x['id']-1 for x in items if x['grade']==level]
 if indices:decisions['levels'][str(level)]+=' '+' '.join(map(str,indices))
for x in items:decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
decisions.update(sourceSha256=sha(after),reviewedRows=len(rows));save(gradepath,decisions)
run(sys.executable,'-X','utf8','scripts/build-shiritori-grade-bands.py')
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=json.loads(coveragepath.read_text(encoding='utf-8'));assert len(coverage)==plan['baselineRows']
for x in items:
 r=rows[x['id']-1];coverage.append(dict(id=x['id'],**{k:r[k] for k in ('reading','word','meaning','level','image_asset')},category='daily-vocabulary-expansion',target=True,scopeReason='2026-10-18の日常語1024語。読みの重複と既存語の別表記を除外。',status='covered',assignment='new',originalId=None))
save(coveragepath,coverage);save(OUT/'plan.json',plan);save(ROOT/'data/dictionary-imports'/(NAME+'.review.json'),items)
summary=dict(date='2026-10-18',baselineRows=plan['baselineRows'],rows=len(rows),addedWords=1024,newReadings=1024,generatedImages=1024,sheets=64,coveredWords=1024,missingImages=0,gradeCounts=dict(collections.Counter(x['grade'] for x in items)),endingNWords=sum(x['gameEndingN'] for x in items),beforeSha256=sha(base),afterSha256=sha(after),r2VerifiedObjects=len(upload['entries']))
save(OUT/'summary.json',summary);save(ROOT/'data/dictionary-imports'/(NAME+'.summary.json'),summary)
reservation=json.loads((OUT/'reservation.json').read_text(encoding='utf-8'));reservation['status']='registered';save(OUT/'reservation.json',reservation)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
