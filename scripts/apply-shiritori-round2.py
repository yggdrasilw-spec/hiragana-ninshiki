"""Apply the second user review; preserve a reversible, hashed history and current row IDs."""
import csv,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/corrections/round2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
path=ROOT/'whitelist.csv'
if (DIR/'ledger.json').exists():
    assert sha(path)==read(DIR/'ledger.json')['afterSha256'],'Later edits exist; do not overwrite them.'
    if '--recrop' in sys.argv:
        manifest=read(ROOT/'assets/shiritori/manifest.json');assets={a['file']:a for a in manifest['assets']}
        for group in read(DIR/'images.json'):
            with Image.open(ROOT/'assets/shiritori/sheets'/group['file']) as im:
                for t in group['tasks']:
                    if not t['file']:continue
                    assert group['visuallyReviewed'] and t.get('cropBox')
                    output=ROOT/'assets/shiritori'/t['file']
                    ImageOps.pad(im.crop(t['cropBox']).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(output,optimize=True)
                    assets[t['file']].update(cropBox=t['cropBox'],prompt=group['prompt'],cropMethod=group['cropMethod'],sha256=sha(output))
        write(ROOT/'assets/shiritori/manifest.json',manifest)
        print('Recorded cell boundaries applied; CSV unchanged.');raise SystemExit(0)
    print('Already applied; hash verified.');raise SystemExit(0)
plan=read(DIR/'plan.json');groups=read(DIR/'images.json')
before_hash=sha(path)
historypath=ROOT/'data/dictionary-imports/history.json';history=read(historypath)
assert history and history[-1]['afterSha256']==before_hash,'Unrecorded dictionary edits exist.'
with path.open(encoding='utf-8',newline='') as f:
    reader=csv.DictReader(f);heads=reader.fieldnames;before=list(reader)
rows=[dict(r) for r in before];coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json')
manifest=read(ROOT/'assets/shiritori/manifest.json');assets={a['file']:a for a in manifest['assets']};replaced={}
for group in groups:
    source=ROOT/'assets/shiritori/sheets'/group['file']
    assert source.exists() and group.get('visuallyReviewed'),'Review and retain each generated sheet before applying.'
    with Image.open(source) as im:
        cols,nrows=group['columns'],group['rows'];cw,ch=im.width/cols,im.height/nrows
        for idx,t in enumerate(group['tasks']):
            if t['file'] is None:continue
            assert t.get('cropBox'),'Measure the actual cell boundaries; generated grids may be uneven.'
            box=t['cropBox']
            ImageOps.pad(im.crop(box).convert('RGB'),(256,256),method=Image.Resampling.LANCZOS,color='white').save(ROOT/'assets/shiritori'/t['file'],optimize=True)
            review=t['visualReview'];assert review
            assets[t['file']]={'file':t['file'],'mode':'asset','credit':'AI生成イラスト','generatedAt':plan['date'],
              'sourceType':'generated-sheet','sourceSheet':'sheets/'+group['file'],'tileIndex':idx+1,'sheetSize':list(im.size),
              'grid':[cols,nrows],'cropBox':box,'cropMethod':group['cropMethod'],'sha256':sha(ROOT/'assets/shiritori'/t['file']),
              'prompt':group['prompt'],'scenePrompt':t['scene'],'review':'目視確認済み: '+review,'status':'reviewed'}
            replaced[t['file']]=review
            for oid in t['ids']:rows[oid-1].update(image_asset='assets/shiritori/'+t['file'],image_mode='asset',image_credit='AI生成イラスト')
for oid,edit in plan['edits'].items():rows[int(oid)-1].update(edit)
removed={int(i):reason for i,reason in plan['delete'].items()}
origins=[i for i in range(1,len(rows)+1) if i not in removed];newids={oid:i for i,oid in enumerate(origins,1)}
current=[rows[i-1] for i in origins];uses={}
for oid,r in zip(origins,current):
    if r['image_asset']:uses.setdefault(Path(r['image_asset']).name,[]).append((oid,r))
# Review every original shared file affected by an order, including uses whose images stay unchanged.
affected={Path(before[i-1]['image_asset']).name for i in plan['orderedIds']}
shared_reviews=read(DIR/'shared-review.json');updated_assets=[]
for file,items in uses.items():
    a=assets[file];r=items[0][1]
    for key in ['reading','word','meaning']:a[key]=r[key]
    oldaliases={e['id']:e for e in a.get('aliases',[])};aliases=[]
    for oid,r in items:
        old=oldaliases.get(oid,{})
        reason=replaced.get(file) or shared_reviews.get(file,{}).get('reason') or old.get('reuseReason','既存の点検記録を維持。')
        aliases.append({'id':newids[oid],'originalId':coverage[oid-1].get('originalId',oid),
          **{k:r[k] for k in ['reading','word','meaning']},'reuseReason':reason,'sourceReview':a['review']})
    a['aliases']=aliases
    if file in affected or file in replaced:a['secondReview']={'date':plan['date'],'scope':'現在の全共有語義との対応と切り出しを確認。','reason':replaced.get(file) or shared_reviews[file]['reason']}
    updated_assets.append(a)
manifest.update(assets=updated_assets,lastCorrectedAt=plan['date'],lastCorrectionRecord='data/corrections/round2/ledger.json')
newcoverage=[]
for oid,r in zip(origins,current):
    e=dict(coverage[oid-1]);e.update(id=newids[oid]);e.update({k:r[k] for k in ['reading','word','meaning','level','image_asset']})
    if oid in plan['orderedIds'] or r!=before[oid-1] or Path(r['image_asset']).name in replaced:
        e['secondCorrectionReview']={'date':plan['date'],'orderId':oid,'image':replaced.get(Path(r['image_asset']).name,'既存画像を語義と照合して維持。'),'meaning':'見出し・読み・説明と画像の対応を確認。'}
    newcoverage.append(e)
with path.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=heads,lineterminator='\n');writer.writeheader();writer.writerows(current)
after_hash=sha(path)
changes=[]
for oid,(old,new) in enumerate(zip(before,rows),1):
    if oid in removed or old!=new:
        changes.append({'originalId':oid,'id':newids.get(oid),'action':'delete' if oid in removed else 'edit','before':old,'after':None if oid in removed else new,'reason':removed.get(oid,'指定注文の語彙・説明または語義に合わせた画像修正。')})
orders=[{'orderId':oid,'id':newids.get(oid),'before':before[oid-1],'after':None if oid in removed else rows[oid-1],
         'action':'delete' if oid in removed else 'correct','reason':removed.get(oid,'語義・説明・画像・共有先を点検。')} for oid in plan['orderedIds']]
ledger={'date':plan['date'],'sourceRows':len(before),'currentRows':len(current),'beforeSha256':before_hash,'afterSha256':after_hash,
 'currentOriginalIds':origins,'changes':changes,'requestedOrders':orders,'sourceImages':len(affected),'replacedImages':list(replaced),
 'removedManifestAssets':sorted(set(assets)-set(uses)),'deletedReasons':plan['delete']}
# Preserve exact before/after lines for historical audits and prevent old batches resurrecting removed words.
def line(r):return ','.join(r[k] for k in heads)
history.append({'type':'vocabulary-corrections','batch':'data/corrections/round2/plan.json','beforeSha256':before_hash,'afterSha256':after_hash,
 'sourceRows':len(before),'currentOriginalIds':origins,'changes':[{'originalId':c['originalId'],'before':line(c['before']),**({'after':line(c['after'])} if c['after'] else {})} for c in changes]})
write(historypath,history);write(DIR/'ledger.json',ledger);write(ROOT/'assets/shiritori/manifest.json',manifest);write(ROOT/'data/image-coverage/review-2026-10-10.json',newcoverage)
# This selection plan explicitly uses live IDs; historical batches and reviews remain historical.
p=ROOT/'data/image-coverage/additional-plan-2026-10-11.json';additional=read(p)
for group in additional['batches']:
    for item in group['items']:item['id']=newids[item['id']]
write(p,additional)
p=ROOT/'data/image-coverage/summary-2026-10-11.json';summary=read(p)
summary.update(vocabularyRows=len(current),totalAssets=len(updated_assets),selectedIds=[t['id'] for g in additional['batches'] for t in g['items']],lastCorrectionRecord='data/corrections/round2/ledger.json')
summary.update(plan['summaryAdjustments'])
write(p,summary)
print(json.dumps({'rows':len(current),'orders':len(orders),'sourceImages':len(affected),'images':len(replaced),'deleted':len(removed)},ensure_ascii=False))
