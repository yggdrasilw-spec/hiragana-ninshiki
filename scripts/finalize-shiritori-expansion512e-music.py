"""Register all 152 approved music pictures together, keeping prior data intact."""
import csv,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-15-expansion512e';OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=read(OUT/'plan.json');music=read(OUT/'music-plan.json');items=[x for x in music['items'] if not x['filler']]
assert len(items)==152
review=read(OUT/'music-semantic-review.json')
assert len(review['sheets'])==10 and all(x['approved'] for x in review['sheets'])
assert {i for s in review['sheets'] for i in s['approvedIds']}=={x['id'] for x in items}
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for sheet in range(1,11):
 group=[x for x in music['items'] if x['sheet']==sheet]
 evidence=grid.verify_report(ROOT/group[0]['cropValidation'],ROOT/'assets/shiritori'/group[0]['sourceSheet'],ROOT/'assets/shiritori')
 assert set(evidence)=={x['filename'] for x in group}
batch=ROOT/'data/batches'/(NAME+'-music-images.csv')
fields=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader()
 for x in items:
  prompt=(OUT/f'music-sheet{x["sheet"]:02}.prompt.txt').read_text(encoding='utf-8')
  if '-v' in x['sourceSheet']:
   prompt+='\nTargeted repair: '+(ROOT/'assets/shiritori'/x['sourceSheet']).with_suffix('.prompt.txt').read_text(encoding='utf-8')
  w.writerow({**{k:x[k] for k in ['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','cropValidation']},'generatedAt':'2026-10-16','prompt':prompt,'credit':'AI生成イラスト'})
subprocess.run([sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(batch)],cwd=ROOT,check=True)
manifestpath=ROOT/'assets/shiritori/manifest.json';manifest=read(manifestpath);lookup={x['file']:x for x in manifest['assets']}
for x in items:
 if x.get('editSourceSheet'):lookup[x['filename']]['editSourceSheet']=x['editSourceSheet']
save(manifestpath,manifest)
byid={x['id']:x for x in items}
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json')
for x in plan['items']:
 if x['id'] not in byid:continue
 picture=byid[x['id']]
 x.update(imageStatus='illustration',filename=picture['filename'],sourceSheet=picture['sourceSheet'],cropValidation=picture['cropValidation'],credit='AI生成イラスト',sheet=picture['sheet'],tileIndex=picture['tileIndex'],scene=picture['scene'],imageReason='楽器の形・奏法または音楽様式の代表的な演奏例を示す独自生成の挿絵。特定の演奏者・ロゴ・既存ジャケットは使わない。')
 coverage[x['id']-1].update(image_asset='assets/shiritori/'+picture['filename'],target=True,status='covered',assignment='new',scopeReason=x['imageReason'])
save(OUT/'plan.json',plan);save(DATA/(NAME+'.review.json'),plan['items'])
save(ROOT/'data/image-coverage/review-2026-10-10.json',coverage)
summary=read(OUT/'summary.json');summary.update(newIllustrations=152,nameCards=360,searchOnly=0,coveredWords=512,missingImages=0,musicSheets=10,unregisteredFillerTiles=8,afterSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest())
save(OUT/'summary.json',summary);save(DATA/(NAME+'.summary.json'),summary)
subprocess.run([sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py'],cwd=ROOT,check=True)
print(json.dumps(summary,ensure_ascii=False))
