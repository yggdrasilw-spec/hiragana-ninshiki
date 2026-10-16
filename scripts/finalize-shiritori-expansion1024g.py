"""Verify saved sheets and atomically prepare the complete 1024-word import."""
import argparse,csv,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-16-expansion1024g'; OUT=ROOT/'data/image-coverage'/NAME
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
REUSE={5:7434,81:140,165:7694,396:1038,693:928,774:257}
def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b if isinstance(b,bytes) else b.encode()).hexdigest()
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--crop-available',action='store_true');parser.add_argument('--import-all',action='store_true');args=parser.parse_args()
if args.prepare:
    assert not (OUT/'plan.json').exists(),'Keep the prepared baseline immutable'
    draft=json.loads((OUT/'draft.json').read_text(encoding='utf-8'))
    baseline=(ROOT/'whitelist.csv').read_bytes();live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')))
    assert len(draft['items'])==1024 and len({x['reading'] for x in draft['items']})==1024
    assert not ({x['reading'] for x in live}&{x['reading'] for x in draft['items']})
    (OUT/'registration-baseline.csv').write_bytes(baseline)
    items=[];fresh=0
    hard=set('アルゴリズム エコロジー 遠近法 確率 寛容 慣用句 丘陵 峡谷 元素 考古学 類推 累積 ルクス ルネサンス ルポルタージュ'.split())
    for slot,x in enumerate(draft['items'],1):
        x=dict(x,slot=slot,id=len(live)+slot,reviewStatus='editorially-reviewed',level=3 if x['word'] in hard else 2)
        x['ageReason']='小学校の生活・読書・教科学習で意味を説明できる語。漢字を含む説明はレベル2。専門的・抽象的な学習語はレベル3。'
        if slot in REUSE:
            src=live[REUSE[slot]-1];x.update(assignment='reused',sourceId=REUSE[slot],filename=Path(src['image_asset']).name,
                imageReason=f"既存ID {REUSE[slot]} の同一見出し・同一語義の別の読み。説明を比較して同じ対象を示す画像を共有。",sourceMeaning=src['meaning'])
        else:
            x.update(assignment='new',sheet=fresh//16+1,tileIndex=fresh%16+1,filename=f"expansion1024g-word-{x['id']}.png",
                imageReason='対象語義の物や具体的な使用・活動場面を示す専用イラスト。説明と組み合わせて意味を伝える。');fresh+=1
        items.append(x)
    plan=dict(batch=NAME,date='2026-10-16',baselineRows=len(live),baselineSha256=sha(baseline),sourceSha256=draft['sourceSha256'],sourceDate=draft['sourceDate'],items=items)
    save(OUT/'plan.json',plan);save(ROOT/'data/dictionary-imports'/(NAME+'.review.json'),items)
    save(ROOT/'data/dictionary-imports'/(NAME+'.source.json'),dict(dictDate=draft['sourceDate'],sourceSha256=draft['sourceSha256'],
        attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',licenseUrl='https://www.edrdg.org/edrdg/licence.html',
        rows=[{k:x[k] for k in ('reading','word','entryId','sourceKana','senseIndex','partOfSpeech','kanaAppliesToKanji','appliesToKana','appliesToKanji')} for x in items]))
    print('Prepared final IDs against '+str(len(live))+' existing rows')
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items'];byslot={x['slot']:x for x in items}
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
selected={}
for p in sorted(OUT.glob('sheet*-staged.json')):
    s=json.loads(p.read_text(encoding='utf-8'))
    if s['passed']:selected[s['sheet']]=s
semantic_path=OUT/'semantic-review.json';semantic=json.loads(semantic_path.read_text(encoding='utf-8')) if semantic_path.exists() else []
approved={x['sourceSheet']:x for x in semantic if x['passed']}
if args.crop_available or args.import_all:
    for n,s in sorted(selected.items()):
        if s['sourceSheet'] not in approved:continue
        names=[Path(byslot[x['slot']]['filename']).stem if not x.get('filler') else f"expansion1024g-unused-{n}-{x['tileIndex']}" for x in s['tiles']]
        report=OUT/(Path(s['sourceSheet']).stem+'-crop.json')
        cmd=[sys.executable,'-B',str(ROOT/'scripts/crop-shiritori-grid.py'),str(ROOT/'assets/shiritori'/s['sourceSheet']),'--names',','.join(names),'--output',str(ROOT/'assets/shiritori'),'--report',str(report)]
        if report.exists():cmd.append('--verify-existing')
        run(*cmd)
        for tile in s['tiles']:
            if tile.get('filler'):continue
            x=byslot[tile['slot']];x.update(sourceSheet=s['sourceSheet'],cropValidation=str(report.relative_to(ROOT)).replace('\\','/'),prompt=s['prompt'],scene=x['word']+'：'+x['meaning'])
    save(OUT/'plan.json',plan)
if not args.import_all:sys.exit()
assert len(selected)==64 and all(s['sourceSheet'] in approved for s in selected.values()),'All 64 source sheets require a real content review'
for n,s in selected.items():
    assert approved[s['sourceSheet']]['approvedSlots']==[t['slot'] for t in s['tiles'] if not t.get('filler')]
    x=next(x for x in items if x.get('sheet')==n)
    grid.verify_report(ROOT/x['cropValidation'],ROOT/'assets/shiritori'/x['sourceSheet'],ROOT/'assets/shiritori')
assert sha((ROOT/'whitelist.csv').read_bytes())==plan['baselineSha256'],'Recheck and rebase if another task changed dictionary'
batch=ROOT/'data/dictionary-imports'/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
    for x in items:w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
save(ROOT/'data/dictionary-imports'/(NAME+'.review.json'),items)
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
imagebatch=ROOT/'data/batches'/(NAME+'-images.csv')
with imagebatch.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
    for x in items:
        if x['assignment']=='new':w.writerow({k:'2026-10-16' if k=='generatedAt' else 'AI生成イラスト' if k=='credit' else x[k] for k in columns})
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
target=ROOT/'whitelist.csv';before=target.read_bytes().decode('utf-8');rows=list(csv.DictReader(target.open(encoding='utf-8')))
manifest_path=ROOT/'assets/shiritori/manifest.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'));assets={a['file']:a for a in manifest['assets']}
for x in items:
    r=rows[x['id']-1];assert all(r[k]==str(x[k]) for k in ('reading','word','meaning','level'))
    if x['assignment']=='reused':
        r.update(image_asset='assets/shiritori/'+x['filename'],image_mode='asset',image_credit='AI生成イラスト')
        assets[x['filename']].setdefault('aliases',[]).append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason=x['imageReason'],sourceReview=assets[x['filename']]['review']))
    assert r['image_asset']=='assets/shiritori/'+x['filename']
    x.update(imageStatus='covered',imageAssignment=x['assignment'])
with target.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(rows)
after=target.read_bytes().decode('utf-8');history_path=ROOT/'data/dictionary-imports/history.json';history=json.loads(history_path.read_text(encoding='utf-8'))
assert history[-1]['afterSha256']==sha(before)
if after!=before:
    changes=[dict(id=i,before=b,after=a) for i,(b,a) in enumerate(zip(before.splitlines()[1:],after.splitlines()[1:]),1) if b!=a]
    assert all(c['id']>plan['baselineRows'] for c in changes)
    history.append(dict(type='image-assets',batches=[str(imagebatch.relative_to(ROOT)),str((OUT/'plan.json').relative_to(ROOT))],beforeSha256=sha(before),afterSha256=sha(after),modifiedLines=changes))
save(history_path,history);save(manifest_path,manifest)
coverage_path=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=json.loads(coverage_path.read_text(encoding='utf-8'))
assert len(coverage)==plan['baselineRows']
for x in items:
    r=rows[x['id']-1];coverage.append(dict(id=x['id'],**{k:r[k] for k in ('reading','word','meaning','level','image_asset')},category='vocabulary-expansion',target=True,scopeReason='2026-10-16追加の別バッチ1024読み。出典と対象語義を個別確認。',status='covered',assignment=x['assignment'],originalId=None))
save(coverage_path,coverage);save(OUT/'plan.json',plan);save(ROOT/'data/dictionary-imports'/(NAME+'.review.json'),items)
assert after.encode().startswith((OUT/'registration-baseline.csv').read_bytes()),'Every preceding row must remain byte-for-byte unchanged'
summary=dict(date='2026-10-16',baselineRows=plan['baselineRows'],rows=len(rows),addedWords=1024,newReadings=1024,generatedImages=1018,reusedExistingWords=6,sheets=64,coveredWords=1024,missingImages=0,
    levels={str(n):sum(x['level']==n for x in items) for n in (1,2,3)},allIds=[x['id'] for x in items],beforeSha256=plan['baselineSha256'],afterSha256=sha(after))
save(OUT/'summary.json',summary);save(ROOT/'data/dictionary-imports'/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py');print(json.dumps(summary,ensure_ascii=False))
