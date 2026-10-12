"""Apply explicitly reviewed spelling variants; preserve reversible dictionary history."""
import argparse,csv,hashlib,io,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/corrections/2026-10-12-variants.json'
def read(p):return json.loads(p.read_text())
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--after-ledger',type=Path);args=parser.parse_args()
if OUT.exists():
    print('Variant merge already recorded; no changes.');raise SystemExit(0)
# (retained before-ID, removed before-ID). Same reading AND same sense verified.
pairs=[(157,158),(205,206),(330,331),(643,1009),(676,677),(772,773),(980,981),(1019,1020),(1178,1179),(1204,1205),(1238,1239),(1437,1438),(1607,1608),(1710,1711),(1763,1764),(1853,1854),(2077,2078),(2234,2235),(2238,2239),(2326,2327),(2532,2533),(2724,2725),(2744,2745),(2763,2764),(3321,3322),(3595,3596),(3906,3907),(5900,5901)]
previouslyMerged=[];preferredImages=set()
if args.after_ledger:
    prior=read(args.after_ledger);mapping={old:new for new,old in enumerate(prior['currentBeforeIds'],1)}
    preferredImages=set(prior.get('imageEdits',{}))
    previouslyMerged=[{'beforeKeepId':k,'beforeDropId':d,'ledger':str(args.after_ledger)} for k,d in pairs if d not in mapping]
    pairs=[(mapping[k],mapping[d]) for k,d in pairs if d in mapping]
path=ROOT/'whitelist.csv';text=path.read_text();reader=csv.DictReader(io.StringIO(text));heads=reader.fieldnames;before=list(reader);rows=[dict(r) for r in before]
histpath=ROOT/'data/dictionary-imports/history.json';hist=read(histpath);assert hist[-1]['afterSha256']==digest(text)
removed={};review=[]
for keep,drop in pairs:
    a,b=rows[keep-1],rows[drop-1];assert a['reading']==b['reading'] and drop not in removed
    a['level']=str(min(int(a['level']),int(b['level'])))
    if b['image_asset'] and (not a['image_asset'] or (Path(b['image_asset']).name in preferredImages and Path(a['image_asset']).name not in preferredImages)):
        for k in ['image_asset','image_mode','image_credit']:a[k]=b[k]
    removed[drop]=keep
    review.append({'beforeKeepId':keep,'beforeDropId':drop,'canonical':a,'variant':b,'reason':'同じ読みで同じ対象・語義を表す表記違い。概要と補足の差は別語義として扱わない。'})
origins=[i for i in range(1,len(rows)+1) if i not in removed];newids={oid:i for i,oid in enumerate(origins,1)};current=[rows[i-1] for i in origins]
for entry in review:entry['id']=newids[entry['beforeKeepId']]
stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=heads,lineterminator='\n');w.writeheader();w.writerows(current);aftertext=stream.getvalue()
changes=[{'beforeId':i,'action':'delete' if i in removed else 'edit','before':old,**({'mergedIntoBeforeId':removed[i]} if i in removed else {'after':rows[i-1]})} for i,old in enumerate(before,1) if i in removed or old!=rows[i-1]]
record={'type':'reviewed-corrections','batch':'data/corrections/2026-10-12-variants.json','beforeSha256':digest(text),'afterSha256':digest(aftertext),'sourceRows':len(before),'currentRows':len(current),'currentBeforeIds':origins,'changes':changes}
manifestpath=ROOT/'assets/shiritori/manifest.json';manifest=read(manifestpath);uses={}
for oid,row in zip(origins,current):
    if row['image_asset']:uses.setdefault(Path(row['image_asset']).name,[]).append((oid,row))
active=[];retired=[]
for a in manifest['assets']:
    if a['file'] not in uses:retired.append(a);continue
    aliases={e['id']:e for e in a.get('aliases',[])};alluses=uses[a['file']]
    main=next((r for _,r in alluses if (r['reading'],r['word'])==(a.get('reading'),a.get('word'))),alluses[0][1]);a.update({k:main[k] for k in ['reading','word','meaning']})
    a['aliases']=[{**aliases.get(oid,{}),'id':newids[oid],**{k:r[k] for k in ['reading','word','meaning']},'reuseReason':aliases.get(oid,{}).get('reuseReason','語義を照合して既存画像を維持。'),'sourceReview':a['review']} for oid,r in alluses]
    active.append(a)
manifest['assets']=active
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragepath)
updated=[]
for oid,r in zip(origins,current):
    e=coverage[oid-1];e.update(id=newids[oid]);e.update({k:r[k] for k in ['reading','word','meaning','level','image_asset']});updated.append(e)
# This plan is live; historical plans and source IDs remain frozen.
p=ROOT/'data/image-coverage/additional-plan-2026-10-11.json';additional=read(p)
for b in additional['batches']:
    for item in b['items']:item['id']=newids[removed.get(item['id'],item['id'])]
write(p,additional)
summarypath=ROOT/'data/image-coverage/summary-2026-10-11.json';summary=read(summarypath);summary.update(vocabularyRows=len(current),totalAssets=len(active),selectedIds=[x['id'] for b in additional['batches'] for x in b['items']]);write(summarypath,summary)
path.write_text(aftertext);hist.append(record);write(histpath,hist);write(manifestpath,manifest);write(coveragepath,updated)
write(OUT,{'date':'2026-10-12','policy':'読みと意味の両方が同じ表記を統合。同音異義語・生物と食用部分・府県と都市は維持。','merged':review,'previouslyMerged':previouslyMerged,'retiredAssets':retired,'history':record})
print(json.dumps({'merged':len(pairs),'rows':len(current),'activeAssets':len(active),'retiredAssets':len(retired)}))
