"""Import only the complete batch approved by the current subject-selection policy."""
import csv,json,hashlib,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'))
review=json.loads((BASE/'content-review.json').read_text(encoding='utf-8'))
assert len(plan)==410 and len({r['id'] for r in plan})==410
assert set(review['acceptedSheets'])==set(range(1,27)), 'Content review incomplete'
baseline=json.loads((BASE/'before-rows.json').read_text(encoding='utf-8'))
current=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig',newline='')))
for item in plan:
 row=current[item['id']-1]
 assert not row['image_asset']
 assert all(row[k]==item[k] for k in ('reading','word','meaning','level'))
 out=BASE/(f'tiles-{item["sheet"]:02}-r{item["revision"]}' if item.get('revision') else f'tiles-{item["sheet"]:02}')
 assert (ROOT/item['cropValidation']).is_file()
 dest=ROOT/'assets/shiritori'/item['filename'];assert not dest.exists()
 shutil.copyfile(out/item['filename'],dest)
fields=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation']
# The crop verifier reproduces all sixteen cells, including unassigned last-sheet fillers.
# These six pebbles are validation evidence only and never enter the manifest/dictionary.
fillers=list((BASE/'tiles-26').glob('wave11-safe-filler-*.png'));assert len(fillers)==6
for filler in fillers:
 dest=ROOT/'assets/shiritori'/filler.name;assert not dest.exists();shutil.copyfile(filler,dest)
batch=ROOT/'data/batches/2026-10-14-wave11-safe-existing410.csv'
with batch.open('w',encoding='utf-8',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(plan)
subprocess.run([sys.executable,'-B',str(ROOT/'scripts/import-shiritori-assets.py'),str(batch)],cwd=ROOT,check=True)
after=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig',newline='')))
assert len(after)==len(current)
ids={r['id'] for r in plan}
for i,(a,b) in enumerate(zip(current,after),1):
 assert all(a[k]==b[k] for k in a if k not in {'image_asset','image_mode','image_credit'})
 if i not in ids:assert a==b
 else:assert b['image_asset'] and b['image_credit']=='AI生成イラスト'
coverage_path=ROOT/'data/image-coverage/review-2026-10-10.json'
coverage=json.loads(coverage_path.read_text(encoding='utf-8'));assert len(coverage)==len(after)
for entry,row in zip(coverage,after):
 if entry['id'] in ids:
  entry['image_asset']=row['image_asset'];entry['assignment']='new';entry['status']='registered'
coverage_path.write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'current-rows.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-B',str(ROOT/'scripts/build-shiritori-review-updates.py')],cwd=ROOT,check=True)
summary={'addedExistingRows':410,'newVocabularyRows':0,'sourceSheets':26,'validationOnlyFillerImages':6,'vocabularyRows':len(after),'registeredRows':sum(bool(r['image_asset']) for r in after),'scopeExistingRows':len(baseline),'scopeMissingBefore':sum(not r['image_asset'] for r in baseline),'scopeMissingAfter':sum(not r['image_asset'] for r in after[:len(baseline)]),'excludedForSubjectPolicy':1359,'editorialPendingRows':25,'previousNonImageColumnsPreserved':True,'previousImagesPreserved':True,'dictionarySha256':hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),'contentReview':'data/image-coverage/2026-10-14-wave11-safe/content-review.json'}
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
