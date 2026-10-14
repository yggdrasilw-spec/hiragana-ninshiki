"""Extract measured grids; validate all 512 words before importing the full batch."""
import argparse,csv,hashlib,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-14-expansion512b'
OUT=ROOT/'data/image-coverage'/NAME
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
parser=argparse.ArgumentParser()
parser.add_argument('--sources',type=Path)
parser.add_argument('--finalize',action='store_true')
parser.add_argument('--version-sheets')
parser.add_argument('--version',default='v2')
args=parser.parse_args()
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
if args.version_sheets:
 numbers={int(n) for n in args.version_sheets.split(',')}
 for x in plan['newImages']:
  if x['sheet'] not in numbers:continue
  x.update(filename=f'expansion512b-{args.version}-word-{x["id"]}.png',sourceSheet=f'sheets/expansion512b-sheet{x["sheet"]:02}-{args.version}.png',
   cropValidation=f'data/image-coverage/{NAME}/sheet{x["sheet"]:02}-{args.version}-crop.json')
  for member in plan['items']:
   if member['id'] in x['sharedIds']:member['filename']=x['filename']
  for member in x['members']:member['filename']=x['filename']
 save(OUT/'plan.json',plan)
if args.sources:
 sources=json.loads(args.sources.read_text(encoding='utf-8'))
 for number,source in sources.items():
  n=int(number);items=[x for x in plan['newImages'] if x['sheet']==n]
  assert len(items)==16
  dest=ROOT/'assets/shiritori'/items[0]['sourceSheet']
  assert not dest.exists() or dest.read_bytes()==Path(source).read_bytes(),'Do not overwrite a saved source sheet.'
  if not dest.exists():shutil.copyfile(source,dest)
  report=ROOT/items[0]['cropValidation']
  (dest.parent/(dest.stem+'.prompt.txt')).write_text(items[0]['prompt'],encoding='utf-8')
  cmd=[sys.executable,'-X','utf8',str(ROOT/'scripts/crop-shiritori-grid.py'),str(dest),'--names',','.join(x['filename'][:-4] for x in items),
   '--output',str(ROOT/'assets/shiritori'),'--report',str(report)]
  if report.exists():cmd.append('--verify-existing')
  result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
  print(json.dumps({'sheet':n,'passed':result.returncode==0,'message':result.stdout+result.stderr},ensure_ascii=False))
if not args.finalize:sys.exit()
semantic=json.loads((OUT/'semantic-review.json').read_text(encoding='utf-8'))
assert len(semantic)==plan['sheets'] and all(x['passed'] and len(x['approvedIds'])==16 and x['notes'] for x in semantic)
reuse=json.loads((OUT/'reuse-review.json').read_text(encoding='utf-8'))
assert set(reuse['approvedIds'])=={x['id'] for x in plan['items'] if x['assignment']=='reused'}
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py')
grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for n in range(1,plan['sheets']+1):
 items=[x for x in plan['newImages'] if x['sheet']==n]
 evidence=grid.verify_report(ROOT/items[0]['cropValidation'],ROOT/'assets/shiritori'/items[0]['sourceSheet'],ROOT/'assets/shiritori')
 assert set(evidence)=={x['filename'] for x in items}
 assert set(next(s['approvedIds'] for s in semantic if s['sheet']==n))=={x['id'] for x in items}
items=plan['items'];assert len(items)==512
byid={x['id']:x for x in items}
for x in plan['newImages']:x['members']=[byid[i] for i in x['sharedIds']]
save(OUT/'plan.json',plan)
batch=ROOT/'data/dictionary-imports'/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
 for x in items:w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
reviews_path=ROOT/'data/dictionary-imports'/(NAME+'.review.json')
reviews=json.loads(reviews_path.read_text(encoding='utf-8'))
for x,r in zip(items,reviews):
 assert all(x[k]==r[k] for k in ('id','reading','word','meaning','level'))
 r.update(imageStatus='covered',filename=x['filename'],imageReason=x['reuseReason'],imageAssignment=x['assignment'],imageSourceId=x['sourceId'])
save(reviews_path,reviews)
baseline=(ROOT/'whitelist.csv').read_bytes()
assert hashlib.sha256(baseline).hexdigest()==plan['baselineSha256'],'Dictionary changed during preparation.'
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
imagebatch=ROOT/'data/batches'/(NAME+'-images.csv')
columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in plan['newImages']:w.writerow({k:('2026-10-14' if k=='generatedAt' else 'AI生成イラスト' if k=='credit' else x[k]) for k in columns})
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
target=ROOT/'whitelist.csv';before=target.read_text(encoding='utf-8')
rows=list(csv.DictReader(target.open(encoding='utf-8')))
manifest_path=ROOT/'assets/shiritori/manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf-8'));assets={a['file']:a for a in manifest['assets']}
for x in items:
 r=rows[x['id']-1]
 assert all(r[k]==str(x[k]) for k in ('reading','word','meaning','level'))
 path='assets/shiritori/'+x['filename']
 assert not r['image_asset'] or r['image_asset']==path
 assert (ROOT/path).is_file() and x['filename'] in assets
 r.update(image_asset=path,image_mode='asset',image_credit=x['credit'])
 a=assets[x['filename']]
 if not any(y['id']==x['id'] for y in a.get('aliases',[])):
  a.setdefault('aliases',[]).append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason=x['reuseReason'],sourceReview=a['review']))
with target.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(rows)
after=target.read_text(encoding='utf-8')
history_path=ROOT/'data/dictionary-imports/history.json'
history=json.loads(history_path.read_text(encoding='utf-8'))
sha=lambda s:hashlib.sha256(s.encode()).hexdigest()
assert history[-1]['afterSha256']==sha(before)
changes=[dict(id=i,before=b,after=a) for i,(b,a) in enumerate(zip(before.splitlines()[1:],after.splitlines()[1:]),1) if b!=a]
assert all(c['id']>plan['baselineRows'] and c['before'].split(',')[:6]==c['after'].split(',')[:6] for c in changes)
history.append(dict(type='image-assets',batches=[str(imagebatch.relative_to(ROOT)),str((OUT/'plan.json').relative_to(ROOT))],beforeSha256=sha(before),afterSha256=sha(after),modifiedLines=changes))
save(history_path,history);save(manifest_path,manifest)
coverage_path=ROOT/'data/image-coverage/review-2026-10-10.json'
coverage=json.loads(coverage_path.read_text(encoding='utf-8'));assert len(coverage)==plan['baselineRows']
for x in items:
 r=rows[x['id']-1]
 coverage.append(dict(id=x['id'],**{k:r[k] for k in ('reading','word','meaning','level','image_asset')},category='vocabulary-expansion',target=True,
  scopeReason='2026-10-14追加の512語。対象語義に合う保存画像を登録。',status='covered',assignment='new' if x['assignment']=='new' else 'reused',originalId=None))
save(coverage_path,coverage)
summary=dict(date='2026-10-14',baselineRows=plan['baselineRows'],rows=len(rows),addedWords=512,newReadings=512,
 levels={str(n):sum(x['level']==n for x in items) for n in (1,2,3)},coveredWords=512,missingImages=0,
 reusedExistingWords=sum(x['assignment']=='reused' for x in items),sharedNewWords=sum(x['assignment']=='shared-new' for x in items),
 generatedImages=len(plan['newImages']),sheets=plan['sheets'],allIds=[x['id'] for x in items],
 beforeSha256=plan['baselineSha256'],afterSha256=sha(after))
assert after.encode().startswith(baseline),'Existing rows must remain byte-for-byte unchanged.'
save(OUT/'summary.json',summary)
save(ROOT/'data/dictionary-imports'/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
