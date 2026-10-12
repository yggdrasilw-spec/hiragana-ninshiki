"""Crop and register the visually reviewed image supplement assets and their research."""
import argparse,csv,hashlib,json,shutil,subprocess
from pathlib import Path
from PIL import Image,ImageOps
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--wave',choices=['wave3','wave4'],default='wave3');args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];DIR=ROOT/f'data/image-coverage/2026-10-12-{args.wave}'
def read(p):return json.loads(p.read_text())
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(DIR/'plan.json');reviews=read(DIR/'image-review.json')
variants=read(ROOT/'data/corrections/2026-10-12-variants.json');ids={old:i for i,old in enumerate(variants['history']['currentBeforeIds'],1)}
for b in plan:
 review=reviews[str(b['batch'])];assert review['visuallyReviewed'];source=Path(review['path']);dest=ROOT/'assets/shiritori/sheets'/f"2026-10-12-{args.wave}-{b['batch']}.png"
 if not dest.exists():shutil.copyfile(source,dest)
 with Image.open(dest) as im:
  w,h=im.size
  for x in b['items']:
   tile=x['tileIndex']-1;cx,cy=tile%4,tile//4
   # Measured grid boundaries can differ from equal quarters; remove divider lines only.
   xs=review.get('columnBoundaries',[round(i*w/4) for i in range(5)])
   ys=review.get('rowBoundaries',[round(i*h/4) for i in range(5)])
   inset=review.get('borderInset',0)
   box=[xs[cx]+inset,ys[cy]+inset,xs[cx+1]-inset,ys[cy+1]-inset]
   x.update(id=x.get('id',ids.get(x['beforeId'])),sourceSheet='sheets/'+dest.name,generatedAt='2026-10-12',cropBox=box,prompt=b['prompt'],visualReview=review['notes'][tile])
   ImageOps.pad(im.crop(box).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(ROOT/'assets/shiritori'/x['filename'],optimize=True)
for repair in reviews['repairs']:
 assert repair['visuallyReviewed'];x=next(x for b in plan for x in b['items'] if x['beforeId']==repair['beforeId']);dest=ROOT/'assets/shiritori/sheets'/repair['filename']
 if not dest.exists():shutil.copyfile(repair['path'],dest)
 with Image.open(dest) as im:
  box=repair.get('cropBox',[0,0,im.width,im.height]);ImageOps.pad(im.crop(box).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(ROOT/'assets/shiritori'/x['filename'],optimize=True)
 x.update(sourceSheet='sheets/'+dest.name,tileIndex=1,cropBox=box,prompt=repair['prompt'],visualReview=repair['review'],repairReason=repair['reason'])
fields=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt'];batch=ROOT/f'data/batches/2026-10-12-{args.wave}-images.csv'
with batch.open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(x for b in plan for x in b['items'])
subprocess.run(['python',str(ROOT/'scripts/import-shiritori-assets.py'),str(batch)],check=True)
manifestpath=ROOT/'assets/shiritori/manifest.json';manifest=read(manifestpath);assets={a['file']:a for a in manifest['assets']}
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragepath);rows=list(csv.DictReader(open(ROOT/'whitelist.csv')))
for b in plan:
 for x in b['items']:
  a=assets[x['filename']];a.update(cropBox=x['cropBox'],cropMethod='Reviewed actual cell boundaries, divider removed only where recorded, aspect ratio preserved with white padding; single image repair where recorded.',prompt=x['prompt'],scenePrompt=x['scene'],review='目視確認済み: '+x['visualReview'],sha256=sha(ROOT/'assets/shiritori'/x['filename']),research=reviews.get('research',{}).get(str(x['beforeId']),{}))
  if x.get('repairReason'):a['repairReason']=x['repairReason']
  for alias in a['aliases']:alias['originalId']=coverage[alias['id']-1].get('originalId');alias['sourceReview']=a['review']
  e=coverage[x['id']-1];e.update(image_asset=rows[x['id']-1]['image_asset'],assignment='new',imageSupplementReview={'wave':args.wave,'review':x['visualReview']})
write(manifestpath,manifest);write(coveragepath,coverage);write(DIR/'registered-plan.json',plan)
summary={'rows':len(rows),'newImages':sum(len(b['items']) for b in plan),'mergedVariants':len(variants['merged']),'referencedImages':len(manifest['assets']),'rowsWithImages':sum(bool(r['image_asset']) for r in rows),'remainingWithoutImages':sum(not r['image_asset'] for r in rows),'remainingEasyWithoutImages':sum(r['level']=='1' and not r['image_asset'] for r in rows),'csvSha256':sha(ROOT/'whitelist.csv'),'repairs':len(reviews['repairs'])}
write(DIR/'summary.json',summary);print(json.dumps(summary,ensure_ascii=False))
