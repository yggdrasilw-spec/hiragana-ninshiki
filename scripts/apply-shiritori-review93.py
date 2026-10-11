"""Apply 103 identity-checked orders, preserving reversible CSV history and image provenance."""
import csv, hashlib, json, shutil, sys
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/corrections/review93-2026-10-11'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
csvpath=ROOT/'whitelist.csv';ledgerpath=DIR/'ledger.json'
if ledgerpath.exists():
    assert read(ledgerpath)['afterSha256']==sha(csvpath),'Later changes exist; do not overwrite with an old plan.'
    if '--refresh-images' in sys.argv:
        ledger=read(ledgerpath);manifest=read(ROOT/'assets/shiritori/manifest.json');assets={a['file']:a for a in manifest['assets']}
        checks={c['file']:c for c in ledger['imageChecks']}
        for group in read(DIR/'generation.json'):
            with Image.open(ROOT/'assets/shiritori/sheets'/group['file']) as im:
                for job in group['tiles']:
                    if job.get('accepted') is False:continue
                    box=job['cropBox'];target=ROOT/'assets/shiritori'/job['file']
                    ImageOps.pad(im.crop(box).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(target,optimize=True)
                    assets[job['file']].update(cropBox=box,sha256=sha(target),resizeMode='contain-with-white-padding')
                    checks[job['file']]['cropBox']=box
        write(ROOT/'assets/shiritori/manifest.json',manifest);write(ledgerpath,ledger)
        print('Refreshed image crops using visually measured boundaries; CSV unchanged.');raise SystemExit(0)
    print('Already applied; reviewed CSV matches ledger.');raise SystemExit(0)
plan=read(DIR/'plan.json');generation=read(DIR/'generation.json')
assert sha(csvpath)==plan['beforeSha256'],'Baseline changed; resolve identities again.'
with csvpath.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);fields=reader.fieldnames;before=list(reader)
rows=[dict(r) for r in before]
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json')
assert len(coverage)==len(before)
resolved={}
for request in plan['requests']:
    matches=[i for i,r in enumerate(rows,1) if r==request['before']]
    assert len(matches)==1 and matches[0]==request['resolvedId'],'Word/reading/meaning/asset identity changed.'
    resolved[request['requestedId']]=matches[0]
manifest=read(ROOT/'assets/shiritori/manifest.json');assets={a['file']:a for a in manifest['assets']}
changedimages={};checks=[]
for group in generation:
    assert group.get('visualReview',{}).get('accepted') is True,'Inspect generated group before applying: '+str(group['number'])
    sheet=ROOT/'assets/shiritori/sheets'/group['file']
    assert sheet.exists(),'Missing saved original sheet.'
    with Image.open(sheet) as im:
        cols=group.get('columns',4);nrows=group.get('rows',4);cw=im.width/cols;ch=im.height/nrows
        for index,job in enumerate(group['tiles']):
            if job.get('accepted') is False:continue
            # Explicit crop boxes may override equal-grid coordinates after visual inspection.
            box=job.get('cropBox',[round((index%cols+.025)*cw),round((index//cols+.025)*ch),round((index%cols+.975)*cw),round((index//cols+.975)*ch)])
            assert 0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height
            target=ROOT/'assets/shiritori'/job['file']
            before_image_hash=sha(target) if target.exists() else None
            ImageOps.pad(im.crop(box).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(target,optimize=True)
            old=assets.get(job['file'])
            if old:
                # Preserve original derivation/prompt before replacing a previously generated image.
                prior={k:v for k,v in old.items() if k!='aliases'}
                prior['sha256']=before_image_hash
            else:prior=None
            sourceuses=[i for i,r in enumerate(before,1) if r['image_asset']==job['source']]
            for requested in job['uses']:
                actual=resolved.get(requested,requested)
                assert actual in sourceuses,'Shared assignment must match source image identity.'
                # A framing repair must not undo an earlier semantic image split.
                if job['kind']=='repair-framing' and rows[actual-1]['image_asset']!=job['source']:continue
                rows[actual-1].update(image_asset='assets/shiritori/'+job['file'],image_mode='asset',image_credit='AI生成イラスト')
            # Reframing updates the existing shared file for all its retained users.
            note=job.get('reviewNote',job['scene'])
            assets[job['file']]=dict(file=job['file'],generatedAt=plan['date'],sourceType='generated-sheet',sourceSheet='sheets/'+group['file'],
                tileIndex=index+1,cropBox=box,sheetSize=list(im.size),grid=[cols,nrows],prompt=group['prompt'],tilePrompt=job['scene'],
                review='目視確認済み: '+note,status='reviewed',mode='asset',credit='AI生成イラスト',sha256=sha(target),resizeMode='contain-with-white-padding',
                revision=dict(date=plan['date'],kind=job['kind'],previousAsset=job['source'],previousProvenance=prior))
            changedimages[job['file']]=note
            checks.append(dict(file=job['file'],sheet=group['file'],tileIndex=index+1,cropBox=box,review=note))
for requested,edits in plan['edits'].items():rows[resolved[int(requested)]-1].update(edits)
for reuse in plan['reuse']:
    actual=resolved[reuse['requestId']];rows[actual-1].update(image_asset=reuse['source'],image_mode='asset',image_credit='AI生成イラスト')
    assets[Path(reuse['source']).name]['revisionReuse']=dict(date=plan['date'],reason=reuse['reason'])
    changedimages[Path(reuse['source']).name]=reuse['reason']
removed={resolved[int(k)]:v for k,v in plan['delete'].items()}
origins=[i for i in range(1,len(rows)+1) if i not in removed]
current=[rows[i-1] for i in origins];newids={old:i for i,old in enumerate(origins,1)}
uses=defaultdict(list)
for old,row in zip(origins,current):
    if row['image_asset']:uses[Path(row['image_asset']).name].append((old,row))
orphaned=sorted(set(assets)-set(uses));newassets=[]
touchedsource={Path(r['before']['image_asset']).name for r in plan['requests']}
for file,shared in uses.items():
    a=assets[file]
    primary=next((r for _,r in shared if r['reading']==a.get('reading') and r['word']==a.get('word')),shared[0][1])
    a.update({k:primary[k] for k in ['reading','word','meaning']})
    previous={x.get('id'):x for x in a.get('aliases',[])}
    aliases=[]
    for old,row in shared:
        prev=previous.get(old,{})
        reuseReason=changedimages.get(file,prev.get('reuseReason','既存画像の共有先。'))
        if file in touchedsource:
            reuseReason=plan.get('sharedReview',{}).get(file,reuseReason)
        aliases.append(dict(id=newids[old],originalId=coverage[old-1].get('originalId',old),preReview93Id=old,
            **{k:row[k] for k in ['reading','word','meaning']},reuseReason=reuseReason,sourceReview=a['review']))
    a['aliases']=aliases
    if file in touchedsource or file in changedimages:
        a['sharedSenseReview']=dict(date=plan['date'],reviewed=True,words=[r['word'] for _,r in shared],
            reason=plan.get('sharedReview',{}).get(file,changedimages.get(file,'既存の場面を確認し、修正後の説明の具体例として整合することを確認。')))
    newassets.append(a)
manifest.update(assets=newassets,lastCorrectedAt=plan['date'])
newcoverage=[]
for old,row in zip(origins,current):
    entry=dict(coverage[old-1]);entry.update(id=newids[old],preReview93Id=old,**{k:row[k] for k in ['reading','word','meaning','level','image_asset']})
    if row!=before[old-1] or Path(row['image_asset']).name in changedimages or Path(before[old-1]['image_asset']).name in touchedsource:
        entry['review93']=dict(date=plan['date'],identityChecked=['word','reading','meaning','image_asset'],
            image=changedimages.get(Path(row['image_asset']).name,'既存画像を確認。修正した語義の具体例として一致。'),status='reviewed')
    newcoverage.append(entry)
changes=[]
for old in range(1,len(rows)+1):
    if old in removed:changes.append(dict(beforeId=old,action='delete',before=before[old-1],reason=removed[old]))
    elif rows[old-1]!=before[old-1]:changes.append(dict(beforeId=old,id=newids[old],action='edit',before=before[old-1],after=rows[old-1]))
with csvpath.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(current)
for request in plan['requests']:
    old=request['resolvedId'];request.update(action='delete' if old in removed else 'edit' if rows[old-1]!=before[old-1] else 'image-or-shared-review',id=newids.get(old),after=None if old in removed else rows[old-1])
ledger=dict(date=plan['date'],baselineCommit=plan['baselineCommit'],beforeSha256=plan['beforeSha256'],afterSha256=sha(csvpath),
    sourceRows=len(before),currentRows=len(current),currentBeforeIds=origins,changes=changes,requests=plan['requests'],
    replacedImages=list(changedimages),removedManifestAssets=orphaned,imageChecks=checks)
historypath=ROOT/'data/dictionary-imports/history.json';history=read(historypath)
assert history[-1]['afterSha256']==plan['beforeSha256']
history.append(dict(type='reviewed-corrections',ledger=str(ledgerpath.relative_to(ROOT)),beforeSha256=ledger['beforeSha256'],afterSha256=ledger['afterSha256'],
    sourceRows=len(before),currentRows=len(current),currentBeforeIds=origins,changes=changes))
write(ledgerpath,ledger);write(historypath,history);write(ROOT/'assets/shiritori/manifest.json',manifest);write(ROOT/'data/image-coverage/review-2026-10-10.json',newcoverage)
print(json.dumps(dict(rows=len(current),orders=len(plan['requests']),modifiedRows=len(changes),images=len(changedimages),deleted=len(removed)),ensure_ascii=False))
