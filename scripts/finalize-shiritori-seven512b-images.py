"""Stage and register the complementary 512 senses after source and delivery checks."""
import argparse,csv,hashlib,importlib.util,json,mimetypes,shutil,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
O=R/'data/image-coverage/2026-10-25-seven512b-images'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sha=lambda x:hashlib.sha256(x).hexdigest()
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==src.read_bytes(),str(dst)
 else:shutil.copyfile(src,dst)
def run(*args):subprocess.run(args,cwd=R,check=True)
parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','register','verify']);parser.add_argument('--staging',type=Path);a=parser.parse_args()
B=a.staging or O/'staging'
spec=importlib.util.spec_from_file_location('grid',R/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
if a.mode=='prepare':
 p=read(B/'plan.json');items=p['items'];assert len(items)==len({x['id'] for x in items})==512
 other=read(R/'data/image-coverage/2026-10-25-seven512-images/plan.json');assert not {x['id'] for x in items}&{x['id'] for x in other['items']}
 baseline=(R/'whitelist.csv').read_bytes();rows=list(csv.DictReader(baseline.decode('utf-8-sig').splitlines()))
 reviews=read(B/'semantic-review-final.json');assert len(reviews)==32 and all(x['passed'] for x in reviews)
 for n in range(1,33):
  chosen=read(B/f'sheet{n:02}.accepted.json');f=B/chosen['folder'];source=f/'source.png';report=f/'crop-validation.json'
  assert reviews[n-1]['sourceSha256']==sha(source.read_bytes())
  verified=grid.verify_report(report,source,f/'tiles');group=[x for x in items if x['sheet']==n]
  stem=f'seven512b-sheet{n:02}-{chosen["folder"].split("-",1)[-1] if "-" in chosen["folder"] else "v1"}'
  source_rel='sheets/'+stem+'.png';proof_rel=str((O/(stem+'-crop.json')).relative_to(R)).replace('\\','/')
  copy(source,R/'assets/shiritori'/source_rel);copy(report,R/proof_rel)
  prompt=(B/(f'sheet{n:02}.reconciled.prompt.txt' if chosen['revision']>=100 else f'sheet{n:02}.prompt.txt')).read_text(encoding='utf8')
  if chosen['revision']==103:prompt=(B/f'sheet{n:02}.regenerate103.prompt.txt').read_text(encoding='utf8')
  edits=[]
  if chosen['revision']==7:edits.append((B/'repair-v7.prompt.txt').read_text(encoding='utf8'))
  if chosen['revision']==8:edits.append(next(x['prompt'] for x in read(B/'sports-repairs.json') if x['n']==n))
  if chosen['revision'] in (9,10):
   edits.append((B/'repair-v7.prompt.txt').read_text(encoding='utf8'))
   edits.append(next(x['prompt'] for x in read(B/'repairs-v9.json') if x['n']==n))
  if chosen['revision']==10:edits.append(next(x['prompt'] for x in read(B/'repairs-v10.json') if x['n']==n))
  if chosen['revision']==101:edits.append(next(x['prompt'] for x in read(B/'reconcile-repairs.json') if x['n']==n))
  if chosen['revision']<100:
   for q in sorted(B.glob(f'sheet{n:02}.edit*.prompt.txt')):edits.append(q.read_text(encoding='utf8'))
  prompt+='\n\nSaved edit instructions (final source is authoritative):\n'+'\n\n'.join(edits)
  (R/'assets/shiritori/sheets'/ (stem+'.prompt.txt')).write_text(prompt,encoding='utf8')
  for x in group:
   row=rows[x['id']-1];assert all(row[k]==x[k] for k in ['reading','word','meaning']);assert not row['image_asset']
   assert verified[x['filename']]['tileIndex']==x['tileIndex'];copy(f/'tiles'/x['filename'],R/'assets/shiritori'/x['filename'])
   x.update(sourceSheet=source_rel,cropValidation=proof_rel,prompt=prompt,scene=x['word']+'：'+x['meaning'],image_asset='assets/shiritori/'+x['filename'],image_mode='asset',image_credit='AI生成イラスト')
  grid.verify_report(R/proof_rel,R/'assets/shiritori'/source_rel,R/'assets/shiritori')
 manifest=read(R/'assets/shiritori/manifest.json');decisions=read(R/'data/shiritori-grade-decisions.json')
 O.mkdir(parents=True,exist_ok=True);(O/'registration-baseline.csv').write_bytes(baseline)
 save(O/'baseline-state.json',dict(dictionarySha256=sha(baseline),rowCount=len(rows),manifestAssets=len(manifest['assets']),manifestPrefixSha256=sha(json.dumps(manifest['assets'],ensure_ascii=False,sort_keys=True).encode()),gradeLevelsSha256=sha(json.dumps(decisions['levels'],sort_keys=True).encode())))
 save(O/'semantic-review.json',reviews);save(O/'plan.json',p)
 copy(B/'plan-v1.json',O/'plan-v1.json')
 paths={R/x['image_asset'] for x in items};paths.update((R/'assets/shiritori/sheets').glob('seven512b-sheet*.png'));paths.update((R/'assets/shiritori/sheets').glob('seven512b-sheet*.prompt.txt'))
 entries=[dict(key=q.relative_to(R).as_posix(),bucket='shiritori-images' if q.parent==R/'assets/shiritori' else 'shiritori-image-archive',bytes=q.stat().st_size,sha256=sha(q.read_bytes()),contentType=mimetypes.guess_type(q.name)[0] or 'text/plain') for q in sorted(paths)]
 assert sum(x['bucket']=='shiritori-images' for x in entries)==512
 save(O/'r2-upload.json',dict(batch=p['batch'],entries=entries))
 cols='id reading word meaning filename scene sourceSheet tileIndex generatedAt prompt cropValidation credit'.split()
 with (R/'data/batches/2026-10-25-seven512b-images.csv').open('w',encoding='utf8',newline='') as stream:
  w=csv.DictWriter(stream,fieldnames=cols,lineterminator='\n');w.writeheader()
  for x in items:w.writerow({k:'2026-10-27' if k=='generatedAt' else 'AI生成イラスト' if k=='credit' else x[k] for k in cols})
 print(json.dumps(dict(prepared=512,objects=len(entries),bytes=sum(x['bytes'] for x in entries))));sys.exit()
p=read(O/'plan.json');items=p['items'];state=read(O/'baseline-state.json');baseline=(O/'registration-baseline.csv').read_bytes()
if a.mode=='register':
 assert (R/'whitelist.csv').read_bytes()==baseline,'Rebase required: dictionary changed after preparation'
 delivery=read(O/'r2-validation.json');assert delivery['complete'] and delivery['publicDownloadedAndSha256Matched']==512
 journal=R/'qa-output/seven512b-images-r2-transfer.jsonl';verified={x['bucket']+'/'+x['key']:x['sha256'] for x in map(json.loads,journal.read_text().splitlines()) if x.get('verified')}
 assert all(verified.get(x['bucket']+'/'+x['key'])==x['sha256'] for x in read(O/'r2-upload.json')['entries'])
 run(sys.executable,'-B','-X','utf8','scripts/import-shiritori-assets.py','data/batches/2026-10-25-seven512b-images.csv')
 decisions=read(R/'data/shiritori-grade-decisions.json');decisions['sourceSha256']=sha((R/'whitelist.csv').read_bytes());save(R/'data/shiritori-grade-decisions.json',decisions)
 coverage=read(R/'data/image-coverage/review-2026-10-10.json')
 for x in items:
  c=coverage[x['id']-1];assert all(c[k]==x[k] for k in ['reading','word','meaning']);c.update(image_asset=x['image_asset'],status='covered',assignment='new',target=True,imageBatch=p['batch'])
 save(R/'data/image-coverage/review-2026-10-10.json',coverage)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-review-updates.py')
 inventory=read(R/'data/image-coverage/r2-assets.json');index={x['key']:x for x in inventory['entries']};index.update({x['key']:x for x in read(O/'r2-upload.json')['entries']});inventory['entries']=sorted(index.values(),key=lambda x:x['key']);inventory['dictionaryImageReferences']=len({x['image_asset'] for x in csv.DictReader((R/'whitelist.csv').open(encoding='utf-8-sig')) if x['image_asset']});inventory['revision']=sha(json.dumps(inventory['entries'],sort_keys=True).encode());save(R/'data/image-coverage/r2-assets.json',inventory)
before=list(csv.DictReader(baseline.decode('utf-8-sig').splitlines()));after=list(csv.DictReader((R/'whitelist.csv').open(encoding='utf-8-sig')));assert len(before)==len(after)==state['rowCount']
ids={x['id'] for x in items};changed=[]
for i,(old,new) in enumerate(zip(before,after),1):
 if old!=new:changed.append(i)
 for k in old:
  if i not in ids or k not in ['image_asset','image_mode','image_credit']:assert old[k]==new[k],(i,k)
assert set(changed)==ids
assets=read(R/'assets/shiritori/manifest.json')['assets'];assert len(assets)==state['manifestAssets']+512
assert sha(json.dumps(assets[:state['manifestAssets']],ensure_ascii=False,sort_keys=True).encode())==state['manifestPrefixSha256']
assert sha(json.dumps(read(R/'data/shiritori-grade-decisions.json')['levels'],sort_keys=True).encode())==state['gradeLevelsSha256']
byfile={x['file']:x for x in assets};coverage=read(R/'data/image-coverage/review-2026-10-10.json')
for n in range(1,33):
 group=[x for x in items if x['sheet']==n];x=group[0];grid.verify_report(R/x['cropValidation'],R/'assets/shiritori'/x['sourceSheet'],R/'assets/shiritori')
 for x in group:
  assert after[x['id']-1]['image_asset']==x['image_asset'];assert coverage[x['id']-1]['image_asset']==x['image_asset'];assert byfile[x['filename']]['sha256']==sha((R/x['image_asset']).read_bytes())
summary=dict(passed=True,registeredImages=512,sourceSheets=32,unchangedVocabularyRows=len(after),unchangedEarlierAssets=state['manifestAssets'],gradeLevelsPreserved=True,publicSha256Matched=512,copyrightedCharactersUsed=False,browserValidation='pending')
if (O/'browser-validation.json').exists() and read(O/'browser-validation.json').get('passed'):
 summary.update(browserValidation='passed',browserViewports=[x['width'] for x in read(O/'browser-validation.json')['results']])
if a.mode!='verify':
 save(O/'summary.json',summary);p['status']='registered';save(O/'plan.json',p)
print(json.dumps(summary))
