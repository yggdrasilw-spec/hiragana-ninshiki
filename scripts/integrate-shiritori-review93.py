"""Resolve the known concurrent review merge, retaining both histories and provenance."""
import csv, hashlib, io, json, subprocess
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/corrections/review93-2026-10-11'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def data(ref,file):return json.loads(git('show',ref+':'+file))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(b):return hashlib.sha256(b).hexdigest()
ours='af4099d';theirs='312878c'
assert git('rev-parse','HEAD').decode().startswith(ours)
assert git('rev-parse','MERGE_HEAD').decode().startswith(theirs),'Only resolves the explicitly reviewed concurrent merge.'
old=data(ours,'data/corrections/review93-2026-10-11/ledger.json')
before_blob=git('show',theirs+':whitelist.csv');reader=csv.DictReader(io.StringIO(before_blob.decode()));heads=reader.fieldnames;before=list(reader)
rows=[dict(r) for r in before];assert len(rows)==6143
resolved={};changes=[]
for c in old['changes']:
    if c['action']=='delete':
        assert not any(r['word']==c['before']['word'] and r['reading']==c['before']['reading'] for r in rows)
        continue
    a,b=c['after'],c['before']
    matches=[i for i,r in enumerate(rows,1) if (r['word'],r['reading']) in [(a['word'],a['reading']),(b['word'],b['reading'])]]
    if c['beforeId']==1105:
        matches=[i for i,r in enumerate(rows,1) if r['word']=='割り込む' and r['reading']=='わりこむ' and r['image_asset']=='assets/shiritori/complete-1131.png']
    assert len(matches)==1,(c['beforeId'],matches)
    i=matches[0];resolved[c['beforeId']]=i
    for key in heads:
        if a[key]!=b[key]:rows[i-1][key]=a[key]
for i,(a,b) in enumerate(zip(rows,before),1):
    if a!=b:changes.append(dict(beforeId=i,id=i,action='edit',before=b,after=a))
csvout=io.StringIO();writer=csv.DictWriter(csvout,fieldnames=heads,lineterminator='\n');writer.writeheader();writer.writerows(rows)
after_blob=csvout.getvalue().encode()
# PNG conflict resolutions only select this task's already reviewed output.
conflicts=git('diff','--name-only','--diff-filter=U').decode().splitlines()
for file in conflicts:
    if file.endswith('.png'):
        assert Path(file).name in old['replacedImages'],file
        (ROOT/file).write_bytes(git('show',ours+':'+file))
main_manifest=data(theirs,'assets/shiritori/manifest.json');our_manifest=data(ours,'assets/shiritori/manifest.json')
assets={a['file']:a for a in main_manifest['assets']}
generated={c['file'] for c in old['imageChecks']}
for a in our_manifest['assets']:
    if a['file'] in generated:assets[a['file']]=a
round2=data(theirs,'data/corrections/round2/ledger.json');snapshots=[]
for file in round2['replacedImages']:
    original=next(a for a in main_manifest['assets'] if a['file']==file)
    archived='sheets/review93-prior-round2-'+file
    (ROOT/'assets/shiritori'/archived).write_bytes(git('show',theirs+':assets/shiritori/'+file))
    snapshots.append({**original,'archivedFile':archived})
coverage=data(theirs,'data/image-coverage/review-2026-10-10.json');ourscoverage=data(ours,'data/image-coverage/review-2026-10-10.json')
assert len(coverage)==len(rows)==len(ourscoverage)
for i,(entry,row) in enumerate(zip(coverage,rows),1):
    entry.update(id=i,**{k:row[k] for k in ['word','reading','meaning','level','image_asset']})
    if 'review93' in ourscoverage[i-1]:entry.update(review93=ourscoverage[i-1]['review93'],preReview93Id=ourscoverage[i-1]['preReview93Id'])
uses=defaultdict(list)
for i,r in enumerate(rows,1):
    if r['image_asset']:uses[Path(r['image_asset']).name].append((i,r))
retired=[a for file,a in assets.items() if file not in uses]
for file in list(assets):
    if file not in uses:del assets[file]
for file,a in assets.items():
    previous={x['id']:x for x in a.get('aliases',[])}
    aliases=[]
    for i,r in uses[file]:
        prev=previous.get(i,{})
        aliases.append({**prev,'id':i,'originalId':coverage[i-1].get('originalId'),**{k:r[k] for k in ['word','reading','meaning']},
            'reuseReason':prev.get('reuseReason',a['review']),'sourceReview':a['review']})
    a['aliases']=aliases
    primary=next((r for _,r in uses[file] if r['word']==a.get('word') and r['reading']==a.get('reading')),uses[file][0][1])
    a.update({k:primary[k] for k in ['word','reading','meaning']})
    if a.get('sharedSenseReview'):a['sharedSenseReview']['words']=[r['word'] for _,r in uses[file]]
    if file=='tsutaeru.png':
        a['sharedSenseReview']=dict(date='2026-10-11',reviewed=True,words=[r['word'] for _,r in uses[file]],reason='mainで追加された口頭の伝達場面を維持。告げる・伝えるに整合する。お話は独立画像にする。')
    if file=='complete-0617.png':
        a['sharedSenseReview']=dict(date='2026-10-11',reviewed=True,words=[r['word'] for _,r in uses[file]],reason='mainで追加された機械を操作する場面を維持。運転の広い語義に合う。機動は独立画像。')
manifest={**main_manifest,**{k:v for k,v in our_manifest.items() if k!='assets'},'assets':list(assets.values()),'previousRound2Assets':snapshots,'supersededRound2Assets':retired}
requests=[]
for request in old['requests']:
    q=dict(request)
    if q['action']=='delete':q['integrationAction']='already-deleted-in-main'
    else:
        target=q['after'];matches=[i for i,r in enumerate(rows,1) if r['word']==target['word'] and r['reading']==target['reading']]
        assert len(matches)==1;(i,)=matches
        q.update(id=i,after=rows[i-1],integrationBeforeId=i)
    requests.append(q)
ledger={**old,'baselineCommit':theirs,'initialBaselineCommit':'b7986ad','beforeSha256':digest(before_blob),'afterSha256':digest(after_blob),
    'sourceRows':len(before),'currentRows':len(rows),'currentBeforeIds':list(range(1,len(rows)+1)),'changes':changes,'requests':requests,
    'removedManifestAssets':[a['file'] for a in retired],
    'integration':dict(mainCommit=theirs,standaloneCommit=ours,policy='mainの非重複変更と画像点検画面の機能を維持し、103注文で変更したフィールドと83枚の点検済み画像を統合。噛みやんはmainで削除済みのため再削除しない。')}
history=data(theirs,'data/dictionary-imports/history.json');assert history[-1]['afterSha256']==digest(before_blob)
history.append(dict(type='reviewed-corrections',ledger='data/corrections/review93-2026-10-11/ledger.json',beforeSha256=ledger['beforeSha256'],afterSha256=ledger['afterSha256'],sourceRows=len(before),currentRows=len(rows),currentBeforeIds=ledger['currentBeforeIds'],changes=changes))
write(DIR/'standalone-ledger.json',old);write(DIR/'ledger.json',ledger);write(ROOT/'assets/shiritori/manifest.json',manifest)
write(ROOT/'data/image-coverage/review-2026-10-10.json',coverage);write(ROOT/'data/dictionary-imports/history.json',history)
(ROOT/'whitelist.csv').write_bytes(after_blob)
# Keep both supported history record formats and both obsolete-vocabulary checks.
s=git('show',ours+':scripts/shiritori-correction-ledger.cjs').decode()
remote=git('show',theirs+':scripts/shiritori-correction-ledger.cjs').decode()
block=remote[remote.index("    if(record.type==='vocabulary-corrections')"):remote.index("    if(record.type==='image-assets')")]
s=s.replace("    if(record.type==='image-assets')",block+"    if(record.type==='image-assets')")
(ROOT/'scripts/shiritori-correction-ledger.cjs').write_text(s)
s=git('show',theirs+':scripts/import-shiritori-words.cjs').decode();our=git('show',ours+':scripts/import-shiritori-words.cjs').decode()
block=our[our.index('const review93File='):our.index('const oldReviewSource=')]
s=s.replace('const oldReviewSource=',block+'const oldReviewSource=');(ROOT/'scripts/import-shiritori-words.cjs').write_text(s)
for file in ['scripts/audit-shiritori-quality.py','tests/shiritori-corrections.cjs']:(ROOT/file).write_bytes(git('show',ours+':'+file))
for file in ['data/image-coverage/README.md','data/image-coverage/summary-2026-10-11.json']:(ROOT/file).write_bytes(git('show',ours+':'+file))
plan=json.loads((DIR/'plan.json').read_text());plan['sharedReview']['tsutaeru.png']=assets['tsutaeru.png']['sharedSenseReview']['reason'];plan['sharedReview']['complete-0617.png']=assets['complete-0617.png']['sharedSenseReview']['reason'];write(DIR/'plan.json',plan)
for entry in coverage:
    if entry.get('review93') and entry['image_asset'] in ['assets/shiritori/tsutaeru.png','assets/shiritori/complete-0617.png']:
        entry['review93']['image']=assets[Path(entry['image_asset']).name]['sharedSenseReview']['reason']
write(ROOT/'data/image-coverage/review-2026-10-10.json',coverage)
print(json.dumps(dict(rows=len(rows),mainPreserved=True,modifiedRows=len(changes),assets=len(assets),archivedRound2Images=len(snapshots)),ensure_ascii=False))
