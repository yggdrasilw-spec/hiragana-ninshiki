"""Finalize a completely reviewed, reproducible vocabulary-and-picture intake."""
import argparse,csv,hashlib,importlib.util,io,json,re,subprocess,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-15-expansion512c';OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
ap=argparse.ArgumentParser();ap.add_argument('--import-all',action='store_true');args=ap.parse_args()
p=read(OUT/'plan.json');items=p['items'];assert len(items)==553
primary=read(DATA/(NAME+'.primary-sources.json'));pairs=read(OUT/'abbreviation-pairs.json')
dictionary_path=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json');dictionary=read(dictionary_path)
entries={e['id']:e for e in dictionary['words']};surfaces={}
canon=lambda s:unicodedata.normalize('NFKC',s).replace(' ','').replace('・','').casefold()
for e in dictionary['words']:
 for f in e['kanji']+e['kana']:
  if not set(f['tags'])<={'sk'}:continue
  form=canon(f['text'])
  if form not in surfaces:surfaces[form]=e['id']
extracted=[]
for x in items:
 sources=[s for s in primary if x['reading'] in s['words'].split()]
 if x.get('entryId'):
  e=entries[x['entryId']]
  # Preserve all applicable senses as evidence; the authored definition, not the
  # first English gloss, selects the sense. HP/MP are explicitly game quantities.
  senses=[i for i,s in enumerate(e['sense']) if ('*' in s['appliesToKana'] or x['sourceKana'] in s['appliesToKana']) and not s['dialect'] and not set(s['misc'])&{'obs','arch','vulg','derog'}]
  if x['reading'] in ('えいちぴー','えむぴー'):senses=[i for i in senses if 'vidg' in e['sense'][i]['field']]
  x['senseEvidenceIndexes']=senses;x['evidenceType']='dictionary-headword'
  extracted.append(dict(id=x['id'],reading=x['reading'],word=x['word'],entryId=e['id'],sourceKana=x['sourceKana'],senseIndexes=senses,
   kana=[k for k in e['kana'] if k['text']==x['sourceKana']],kanji=e['kanji'],senseEvidence=[e['sense'][i] for i in senses]))
 elif sources:
  x.update(lexicalSource='一次資料の名称・用例を確認。'+sources[0]['url'],sources=[s['url'] for s in sources],evidenceType='primary-source')
 else:
  # These are ordinary transparent compounds or short forms. Do not label them
  # independently attested dictionary entries or turn frequency into age proof.
  related=[]
  for f in (x['word'],x['word'].replace('グリーク','ギリシャ')):
   f=canon(f)
   for n in range(min(len(f),14),1,-1):
    for start in range(len(f)-n+1):
     part=f[start:start+n]
     if part in surfaces and not any(part in a['form'] for a in related):related.append(dict(form=part,entryId=surfaces[part]))
  x.update(lexicalSource='一般的な複合語・通称として語形と用途を編集確認。独立した辞書見出しの確認とは区別。',
   evidenceType='compound-or-short-form-editorial',componentEvidence=related[:8],sources=['https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+v['entryId'] for v in related[:8]])
 if sources:
  x['primaryEvidence']=sources
  x['sources']=list(dict.fromkeys(x.get('sources',[])+[s['url'] for s in sources]))
 x.update(imageStatus='covered',imageReason=x['reuseReason'],imageAssignment=x['assignment'])
 x['abbreviationRelations']=[r for r in pairs if x['reading'] in (r['abbreviation'],r['fullReading'])]
for pair in pairs:
 pair['relation']='origin' if pair['abbreviation']=='きゅーあーるこーど' else 'compound-components' if pair['abbreviation'] in ('ぬいかつ','おしかつ') else 'common-name' if pair['abbreviation'] in ('がちゃ','がちゃがちゃ','じーぱん','ぶれいきん') else 'abbreviation-or-short-form'
 if pair['abbreviation']=='きゅーあーるこーど':pair['note']='QRコードは正式名称。クイックレスポンスは由来の語であり展開した正式名ではない。'
 if pair['abbreviation'] in ('ぬいかつ','おしかつ'):pair['note']='ぬいぐるみ／推しと活動の複合。語数のための「ぬいぐるみ活動」「推し活動」は新造しない。'
for x in items:x['abbreviationRelations']=[r for r in pairs if x['reading'] in (r['abbreviation'],r['fullReading'])]
save(OUT/'abbreviation-pairs.json',pairs)
save(DATA/(NAME+'.review.json'),items)
save(DATA/(NAME+'.source.json'),dict(dictDate=dictionary['dictDate'],sourceSha256=hashlib.sha256(dictionary_path.read_bytes()).hexdigest(),
 attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',licenseUrl='https://www.edrdg.org/edrdg/licence.html',
 rows=extracted,primarySources=primary,policy='構成語のみの根拠は独立見出し確認と区別。意味と児童適合性は独自に編集確認。'))
save(OUT/'plan.json',p)
if not args.import_all:
 print(json.dumps(dict(words=len(items),evidence={t:sum(x['evidenceType']==t for x in items) for t in sorted({x['evidenceType'] for x in items})}),ensure_ascii=False));sys.exit()
semantic=read(OUT/'semantic-review.json')
assert all(x['passed'] for x in semantic['illustrations']) and len(semantic['illustrations'])==p['sheets']
assert set(semantic['approvedDiagramIds'])=={x['id'] for x in p['diagrams']}
assert set(semantic['approvedReuseIds'])=={x['id'] for x in items if x['assignment']=='reused'}
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for n in range(1,p['sheets']+1):
 tiles=[x for x in p['newImages'] if x['sheet']==n]
 evidence=grid.verify_report(ROOT/tiles[0]['cropValidation'],ROOT/'assets/shiritori'/tiles[0]['sourceSheet'],ROOT/'assets/shiritori')
 assert {x['filename'] for x in tiles}<={*evidence}
 assert set(next(s['approvedIds'] for s in semantic['illustrations'] if s['sheet']==n))=={x['id'] for x in tiles}
baseline=(ROOT/'whitelist.csv').read_text(encoding='utf-8');assert sha(baseline)==p['baselineSha256']
batch=DATA/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
 for x in items:w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only');run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
imagebatch=ROOT/'data/batches'/(NAME+'-images.csv')
columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in p['newImages']+p['diagrams']:w.writerow({k:('2026-10-15' if k=='generatedAt' else x.get(k,'')) for k in columns})
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
target=ROOT/'whitelist.csv';before=target.read_text(encoding='utf-8');rows=list(csv.DictReader(io.StringIO(before)))
manifestpath=ROOT/'assets/shiritori/manifest.json';manifest=read(manifestpath);assets={a['file']:a for a in manifest['assets']}
for x in items:
 row=rows[x['id']-1];assert all(str(x[k])==row[k] for k in ('reading','word','meaning','level'))
 assert x['filename'] in assets and (ROOT/'assets/shiritori'/x['filename']).is_file()
 row.update(image_asset='assets/shiritori/'+x['filename'],image_mode='asset',image_credit=x['credit'])
 a=assets[x['filename']]
 source_item=next((s for s in p['newImages'] if s['filename']==x['filename']),None)
 if source_item and source_item.get('editSourceSheet'):a['editSourceSheet']=source_item['editSourceSheet']
 if not any(y['id']==x['id'] for y in a.get('aliases',[])):a.setdefault('aliases',[]).append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason=x['reuseReason'],sourceReview=a['review']))
buffer=io.StringIO(newline='');w=csv.DictWriter(buffer,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(rows);after=buffer.getvalue()
assert after.startswith(baseline),'All pre-existing rows must be unchanged.'
historypath=DATA/'history.json';history=read(historypath);assert history[-1]['afterSha256']==sha(before)
history.append(dict(type='image-assets',batches=[str(imagebatch.relative_to(ROOT)),str((OUT/'plan.json').relative_to(ROOT))],beforeSha256=sha(before),afterSha256=sha(after),modifiedLines=[dict(id=i,before=b,after=a) for i,(b,a) in enumerate(zip(before.splitlines()[1:],after.splitlines()[1:]),1) if b!=a]))
target.write_text(after,encoding='utf-8',newline='\n');save(historypath,history);save(manifestpath,manifest)
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(rows[x['id']-1] for x in items)
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragepath);assert len(coverage)==p['baselineRows']
for x in items:
 row=rows[x['id']-1];coverage.append(dict(id=x['id'],**{k:row[k] for k in ('reading','word','meaning','level','image_asset')},category='vocabulary-expansion',target=True,
  scopeReason='2026-10-15追加の略語・一文字語・身近な新語と元の言葉。',status='covered',assignment='reused' if x['assignment']=='reused' else 'new',originalId=None))
save(coveragepath,coverage)
summary=dict(date='2026-10-15',baselineRows=p['baselineRows'],rows=len(rows),addedWords=len(items),newReadings=len({x['reading'] for x in items}),singleCharacterWords=sum(len(x['reading'])==1 for x in items),endingN=sum(x['reading'].endswith('ん') for x in items),
 abbreviationRelations=len(pairs),coveredWords=len(items),missingImages=0,newIllustrations=len(p['newImages']),newDiagrams=len(p['diagrams']),newImageFiles=len(p['newImages'])+len(p['diagrams']),
 reusedExistingWords=sum(x['assignment']=='reused' for x in items),sharedNewWords=sum(x['assignment']=='shared-new' for x in items),sheets=p['sheets'],levels={str(n):sum(x['level']==n for x in items) for n in (1,2,3)},allIds=[x['id'] for x in items],beforeSha256=sha(baseline),afterSha256=sha(after))
save(OUT/'summary.json',summary);save(DATA/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
