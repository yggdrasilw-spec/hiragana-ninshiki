"""Crop measured grids and import only after all semantic reviews are present."""
import argparse,csv,hashlib,importlib.util,io,json,subprocess,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-16-expansion1024f';OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def run(*a):subprocess.run(a,cwd=ROOT,check=True)
def writecsv(p,rows,fields):
 with p.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
ap=argparse.ArgumentParser();ap.add_argument('--crop',action='store_true');ap.add_argument('--import-all',action='store_true');args=ap.parse_args()
plan=read(OUT/'plan.json');items=plan['items']
revisions={n:2 for n in [6,7,8,9,10,14,15,16,19,22,23,25,26,28]};revisions.update({11:3,13:3,21:4,30:3,31:3,32:4,33:3})
def version_suffix(n):return '-v'+str(revisions[n]) if n in revisions else ''
def sheet_stem(n):return f'expansion1024f-sheet{n:02}'+version_suffix(n)
def report_name(n):return f'sheet{n:02}'+version_suffix(n)+'-crop.json'
baseline=OUT/'baseline.csv'
if not baseline.exists():baseline.write_text((ROOT/'whitelist.csv').read_text(encoding='utf-8'),encoding='utf-8')
before=baseline.read_text(encoding='utf-8');old=list(csv.DictReader(io.StringIO(before)))
for x in items:
 x['id']=len(old)+x['slot'];x['filename']=(f'expansion1024fv{revisions[x["sheet"]]}-word-{x["id"]}.png' if x.get('sheet') in revisions else f'expansion1024f-word-{x["id"]}.png') if x.get('sheet') else None
by_slot={x['slot']:x for x in items}
for x in items:
 if x.get('reuseSlot'):x['filename']=by_slot[x['reuseSlot']]['filename']
plan.update(baselineRows=len(old),beforeSha256=sha(before));save(OUT/'plan.json',plan)
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
ready=[]
for n in range(1,plan['sheets']+1):
 sheet=ROOT/'assets/shiritori/sheets'/(sheet_stem(n)+'.png');report=OUT/report_name(n)
 if not sheet.exists():continue
 group=sorted([x for x in items if x.get('sheet')==n],key=lambda x:x['tileIndex'])
 names=[x['filename'][:-4] for x in group]
 while len(names)<16:names.append(f'expansion1024f-padding-{n:02}-{len(names)+1:02}')
 if not report.exists():
  if not args.crop:continue
  result=subprocess.run([sys.executable,'-X','utf8','scripts/crop-shiritori-grid.py',str(sheet),'--names',','.join(names),'--output','assets/shiritori','--report',str(report)],cwd=ROOT)
  if result.returncode:continue
 grid.verify_report(report,sheet,ROOT/'assets/shiritori');ready.append(n)
 prompt=(OUT/(f'sheet{n:02}'+version_suffix(n)+'.prompt.txt')).read_text(encoding='utf-8');sheet.with_suffix('.prompt.txt').write_text(prompt,encoding='utf-8')
print(json.dumps(dict(cropped=len(ready),sheets=plan['sheets'],baselineRows=len(old)),ensure_ascii=False),flush=True)
if not args.import_all:sys.exit(0)
assert len(ready)==plan['sheets'],'Finish all measured crops before importing'
semantic=read(OUT/'semantic-review.json');assert {x['sheet'] for x in semantic if x['passed']}==set(ready),'Review every source sheet before importing'
live_text=(ROOT/'whitelist.csv').read_text(encoding='utf-8');assert live_text==before,'Live dictionary changed; rebase IDs and crop evidence before importing'
assert read(DATA/'history.json')[-1]['afterSha256']==sha(before)
reviews=[];batch=[];image_rows=[]
source_audit=read(OUT/'source-audit.json');evidence={x['slot']:x for x in source_audit['rows']}
for x in items:
 explanation=x['imagePolicy']=='none'
 review=dict(x,lexicalSource='公式の製品・競技・天体一覧または伝承資料を参照し独自編集した名称。出典一覧と個別照合状況はsource-audit.jsonを参照。',meaningReason='対象・分類・メーカー・遊び方を区別して独自作成。 '+x['meaning'],ageReason='身近な商品名や知っている子が使う発展語はレベル3。一般の道具や競技はレベル2。',imageReason='ユーザー指定により説明のみ。保存画像も外部検索も使わない。' if explanation else '伝承・科学上の特徴または定義に基づく独自の教育用イラスト。同音の別の対象と画像を共有しない。天体の表面は写真ではなく概念図。',imageStatus='intentionally-omitted' if explanation else 'covered',reviewStatus='editorially-reviewed',definitionAuthor='独自作成（2026-10-16）')
 if x['word'] in ['ヨーグレット','ハイレモン']:review['sources']=['https://www.atrion-s.com/products/page/1']
 review['sources']=evidence[x['slot']]['sources']
 if 'dictionaryEvidence' in evidence[x['slot']]:review['dictionaryEvidence']=evidence[x['slot']]['dictionaryEvidence']
 reviews.append(review)
 batch.append(dict(reading=x['reading'],word=x['word'],meaning=x['meaning'],imagequery=x['word'],level=x['level'],imagequery_en='',image_asset='',image_mode='none' if explanation else '',image_credit='説明のみ（画像なし・外部検索なし）' if explanation else ''))
 if x.get('sheet'):
  prompt=(ROOT/'assets/shiritori/sheets'/(sheet_stem(x['sheet'])+'.prompt.txt')).read_text(encoding='utf-8')
  image_rows.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],filename=x['filename'],scene=x['word']+'：'+x['meaning'],sourceSheet='sheets/'+sheet_stem(x['sheet'])+'.png',tileIndex=x['tileIndex'],generatedAt='2026-10-16',prompt=prompt,cropValidation=f'data/image-coverage/{NAME}/'+report_name(x['sheet']),credit='AI生成イラスト'))
save(DATA/(NAME+'.review.json'),reviews)
save(DATA/(NAME+'.source.json'),dict(date='2026-10-16',rows=source_audit['rows'],browserCheckedPages=source_audit['browserCheckedPages'],retrievalNote=source_audit['retrievalNote']))
writecsv(DATA/(NAME+'.csv'),batch,HEADER)
image_csv=ROOT/'data/batches'/(NAME+'-images.csv');writecsv(image_csv,image_rows,list(image_rows[0]))
run('node','scripts/import-shiritori-words.cjs',str(DATA/(NAME+'.csv')),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(DATA/(NAME+'.csv')),'--append')
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(image_csv))
text=(ROOT/'whitelist.csv').read_text(encoding='utf-8');rows=list(csv.DictReader(io.StringIO(text)));manifest=read(ROOT/'assets/shiritori/manifest.json');assets={x['file']:x for x in manifest['assets']}
for x in items:
 if not x.get('reuseSlot'):continue
 row=rows[x['id']-1];row.update(image_asset='assets/shiritori/'+x['filename'],image_mode='asset',image_credit='AI生成イラスト')
 assets[x['filename']]['aliases'].append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason='同じ対象を指す別名・略称。',sourceReview='この語義が共有元と同じ対象を指すことを確認。'))
# An already registered concrete candy is also subject to the requested no-image rule.
prior_policy=[]
for i,row in enumerate(rows[:len(old)],1):
 if row['word']=='チロルチョコ' and not row['image_asset']:
  prior_policy.append(dict(id=i,word=row['word']));row.update(image_mode='none',image_credit='説明のみ（画像なし・外部検索なし）')
buffer=io.StringIO();w=csv.DictWriter(buffer,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(rows);after=buffer.getvalue()
history=read(DATA/'history.json');assert history[-1]['afterSha256']==sha(text)
if after!=text:
 history.append(dict(type='image-assets',batches=[str(image_csv.relative_to(ROOT))],beforeSha256=sha(text),afterSha256=sha(after),modifiedLines=[dict(id=i,before=a,after=b) for i,(a,b) in enumerate(zip(text.splitlines()[1:],after.splitlines()[1:]),1) if a!=b],note='別名の画像割り当てと、既存チロルチョコの外部画像検索抑止。'))
 (ROOT/'whitelist.csv').write_text(after,encoding='utf-8',newline='\n');save(DATA/'history.json',history)
save(ROOT/'assets/shiritori/manifest.json',manifest)
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');byid={r['id']:r for r in coverage}
for x in items:
 row=rows[x['id']-1];byid[x['id']]=dict(id=x['id'],**row,target=x['imagePolicy']!='none',category=x['category'],scopeReason='具体的な商品・会社名は説明のみ。一般の対象は独自イラスト。',assignment='reused' if x.get('reuseSlot') else 'new' if x['imagePolicy']!='none' else 'explanation-only',sourceId=by_slot[x['reuseSlot']]['id'] if x.get('reuseSlot') else x['id'],sourceReview='語義ごとの画像方針を記録。')
for x in prior_policy:byid[x['id']].update(rows[x['id']-1])
save(ROOT/'data/image-coverage/review-2026-10-10.json',[byid[i] for i in range(1,len(rows)+1)])
summary=dict(name=NAME,addedWords=len(items),distinctNewReadings=len(set(x['reading'] for x in items)-{x['reading'] for x in old}),baselineRows=len(old),totalRows=len(rows),categories=dict(Counter(x['category'] for x in items)),newIllustrations=plan['newIllustrations'],reusedIllustrations=plan['reuse'],explanationOnly=plan['explanationOnly'],missingRequiredImages=sum(x['imagePolicy']!='none' and not rows[x['id']-1]['image_asset'] for x in items),priorPolicyUpdates=prior_policy,beforeSha256=sha(before),afterSha256=sha(after))
save(OUT/'summary.json',summary);save(DATA/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py');print(json.dumps(summary,ensure_ascii=False))
