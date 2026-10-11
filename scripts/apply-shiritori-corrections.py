"""Apply reviewed corrections once; reruns verify instead of reverting later edits."""
import csv, hashlib, json, re, shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/corrections'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
csv_path=ROOT/'whitelist.csv'; ledger_path=DIR/'2026-10-11-ledger.json'
if ledger_path.exists():
    assert read(ledger_path)['afterSha256']==digest(csv_path),'Later edits exist; do not reapply an old plan.'
    print('Already applied; CSV matches the reviewed result.');raise SystemExit(0)
plan=read(DIR/'2026-10-11-plan.json');groups=read(DIR/'2026-10-11-images.json')
with csv_path.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);fields=reader.fieldnames;before=list(reader)
rows=[dict(r) for r in before]
manifest=read(ROOT/'assets/shiritori/manifest.json');assets={a['file']:a for a in manifest['assets']}
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');replaced={}
for group in groups:
    sheet=ROOT/'assets/shiritori/sheets'/group['file']
    if not sheet.exists(): shutil.copyfile(group['source'],sheet)
    with Image.open(sheet) as im:
        width,height=im.size;cols=group['columns'];nrows=group['rows']
        for i,(file,ids,review) in enumerate(group['tiles']):
            if file is None: continue
            x,y=i%cols,i//cols;cw,ch=width/cols,height/nrows
            box=(round((x+.018)*cw),round((y+.018)*ch),round((x+.982)*cw),round((y+.982)*ch))
            im.crop(box).convert('RGB').resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'assets/shiritori'/file,optimize=True)
            for id in ids:rows[id-1].update(image_asset='assets/shiritori/'+file,image_mode='asset',image_credit='AI生成イラスト')
            assets[file]={'file':file,'generatedAt':plan['date'],'sourceType':'generated-sheet','sourceSheet':'sheets/'+group['file'],
                'tileIndex':i+1,'cropBox':list(box),'sheetSize':[width,height],'grid':[cols,nrows],'prompt':group['prompt'],
                'review':'目視確認済み: '+review,'status':'reviewed','mode':'asset','credit':'AI生成イラスト'}
            replaced[file]=review
for sid,edits in plan['edits'].items():rows[int(sid)-1].update(edits)
removed={int(id):{'action':'delete','reason':reason} for id,reason in plan['delete'].items()}
for drop,keep in plan['merge']:
    assert rows[drop-1]['reading']==rows[keep-1]['reading'] and drop not in removed
    removed[drop]={'action':'merge','mergedIntoOriginalId':keep,'reason':'同じ語義の表記違いを統合。'}
    rows[keep-1]['level']=str(min(int(rows[keep-1]['level']),int(rows[drop-1]['level'])))
    if not rows[keep-1]['image_asset'] and rows[drop-1]['image_asset']:
        for key in ['image_asset','image_mode','image_credit']:rows[keep-1][key]=rows[drop-1][key]
auto=[]
for oid,row in enumerate(rows,1):
    if oid in removed:continue
    for word in dict.fromkeys([row['word'],row['reading']]):
        prefix=re.match(r'^'+re.escape(word)+r'は[、\s]*',row['meaning'])
        if prefix and len(row['meaning'][prefix.end():])>=8:
            row['meaning']=row['meaning'][prefix.end():];auto.append(oid);break
origins=[i for i in range(1,len(rows)+1) if i not in removed];current=[rows[i-1] for i in origins]
newids={oid:i for i,oid in enumerate(origins,1)};byfile={}
for oid,row in zip(origins,current):
    if row['image_asset']:byfile.setdefault(Path(row['image_asset']).name,[]).append((oid,row))
orphaned=sorted(set(assets)-set(byfile));newassets=[]
for file,uses in byfile.items():
    a=assets[file];oid,row=next(((o,r) for o,r in uses if r['reading']==a.get('reading') and r['word']==a.get('word')),uses[0])
    for key in ['reading','word','meaning']:a[key]=row[key]
    a['aliases']=[{'id':newids[o],'originalId':o,**{k:r[k] for k in ['reading','word','meaning']},
        'reuseReason':replaced.get(file,'既存の共有画像。全語義の追加確認候補は品質監査レポートを参照。'),
        'sourceReview':a['review']} for o,r in uses]
    newassets.append(a)
manifest.update(assets=newassets,lastCorrectedAt=plan['date'])
newcoverage=[]
for oid,row in zip(origins,current):
    entry=dict(coverage[oid-1]);entry.update(id=newids[oid],originalId=oid)
    for key in ['reading','word','meaning','level','image_asset']:entry[key]=row[key]
    if row!=before[oid-1]:entry['correctionReview']={'date':plan['date'],'image':replaced.get(Path(row['image_asset']).name,'既存画像を維持。'),'meaning':'語義・表記・冒頭の反復を修正。'}
    newcoverage.append(entry)
before_hash=digest(csv_path)
with csv_path.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(current)
changes=[]
for oid,(old,new) in enumerate(zip(before,rows),1):
    if oid in removed:changes.append({'originalId':oid,'before':old,**removed[oid]})
    elif old!=new or Path(new['image_asset']).name in replaced:changes.append({'originalId':oid,'id':newids[oid],'action':'edit','before':old,'after':new,
        'reason':'指定注文・共有画像の分離・語義修正。' if str(oid) in plan['edits'] or old['image_asset']!=new['image_asset'] else '冒頭の見出し語の単純な繰り返しを除去。'})
ledger={'date':plan['date'],'policy':plan['policy'],'beforeSha256':before_hash,'afterSha256':digest(csv_path),
    'sourceRows':len(before),'currentRows':len(current),'currentOriginalIds':origins,'changes':changes,
    'removedManifestAssets':orphaned,'replacedImages':list(replaced),'automaticSubjectCleanup':auto}
write(ledger_path,ledger);write(ROOT/'assets/shiritori/manifest.json',manifest);write(ROOT/'data/image-coverage/review-2026-10-10.json',newcoverage)
print(json.dumps({'rows':len(current),'deleted':len(plan['delete']),'merged':len(plan['merge']),'images':len(replaced),'automaticExplanationCleanups':len(auto)},ensure_ascii=False))
