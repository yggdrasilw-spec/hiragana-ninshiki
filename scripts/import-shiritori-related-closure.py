"""Append source-related forms and structurally verified compounds, conservatively.

No translation inherited through ambiguous English-only WordNet alignment is
adopted. These additions stay at level 4 pending individual age/sense review.
"""
import collections,csv,hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion'
BATCH=sys.argv[sys.argv.index('--batch')+1] if '--batch' in sys.argv else '2026-11-16-related-closure'
if not re.fullmatch(r'2026-11-16-related-closure(?:-\d+)?',BATCH):raise ValueError('Unexpected batch name')
BASE=R/'data/dictionary-imports'/BATCH
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(*args):subprocess.run(args,cwd=R,check=True)
def finish_registration(summary,reviews,entries):
 after=(R/'whitelist.csv').read_bytes();history=read(R/'data/dictionary-imports/history.json');record=history[-1]
 assert str(record['batch']).replace('\\','/')=='data/dictionary-imports/'+BATCH+'.csv'
 assert record['beforeSha256']==summary['baselineSha256'] and record['afterSha256']==sha(after)
 before=b'\n'.join(after.splitlines()[:summary['baselineRows']+1])+b'\n'
 assert sha(before)==summary['baselineSha256'],'Existing prefix changed'
 getkey=lambda x:(x['reading'],x['word'],x['meaning'])
 actualkeys=[tuple(line.split(',')[:3]) for line in record['addedLines']]
 allowed={getkey(x):x for x in reviews};entrymap={getkey(x):x for x in entries}
 assert len(actualkeys)==len(set(actualkeys)) and set(actualkeys)<=set(allowed)
 holds=read(BASE.with_suffix('.held.json'))
 for x in reviews:
  if getkey(x) not in set(actualkeys):holds.append(dict(word=x['word'],reading=x['reading'],reason='取り込み元の訂正履歴で廃止済みの語義・表記。復活させず除外。'))
 reviews=[dict(allowed[key],id=summary['baselineRows']+i+1) for i,key in enumerate(actualkeys)]
 entries=[entrymap[key] for key in actualkeys]
 save(BASE.with_suffix('.review.json'),reviews);save(BASE.with_suffix('.entries.json'),entries);save(BASE.with_suffix('.held.json'),holds)
 header=after.decode('utf-8').splitlines()[0]
 BASE.with_suffix('.csv').write_text(header+'\n'+'\n'.join(record['addedLines'])+'\n',encoding='utf-8')
 oldread={x['reading'] for x in csv.DictReader(before.decode('utf-8').splitlines())}
 dfile=R/'data/shiritori-grade-decisions.json';d=read(dfile)
 assert d['sourceSha256']==summary['baselineSha256'] and d['reviewedRows']==summary['baselineRows']
 for x in reviews:d['levels']['4']+=' '+str(x['id']-1)
 d.update(sourceSha256=sha(after),reviewedRows=summary['baselineRows']+len(reviews));save(dfile,d)
 summary.update(registered=True,afterSha256=sha(after),totalRows=summary['baselineRows']+len(reviews),added=len(reviews),held=len(holds),
  newReadings=len({x['reading'] for x in reviews}-oldread),existingReadings=len({x['reading'] for x in reviews}&oldread),kinds=dict(collections.Counter(x['kind'] for x in reviews)))
 save(BASE.with_suffix('.summary.json'),summary)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
 summary['deliveryBuilt']=True;save(BASE.with_suffix('.summary.json'),summary);print(json.dumps(summary,ensure_ascii=False))
def main():
 sf=BASE.with_suffix('.summary.json')
 if sf.exists() and read(sf).get('registered'):
  s=read(sf)
  if not s.get('deliveryBuilt'):run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');s['deliveryBuilt']=True;save(sf,s)
  print(json.dumps(dict(alreadyRegistered=True,added=s['added'])));return
 if sf.exists() and '--apply' in sys.argv:
  s=read(sf);last=read(R/'data/dictionary-imports/history.json')[-1]
  if str(last.get('batch','')).replace('\\','/')=='data/dictionary-imports/'+BATCH+'.csv':
   finish_registration(s,read(BASE.with_suffix('.review.json')),read(BASE.with_suffix('.entries.json')));return
 before=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(before.decode('utf-8-sig').splitlines()));pairs={(x['reading'],x['word']) for x in old};oldread={x['reading'] for x in old}
 for file in (R/'data/dictionary-imports').glob('2026-11-16-related-closure*.held.json'):
  for x in read(file):
   if '廃止済み' in x.get('reason',''):pairs.add((x['reading'],x['word']))
 byexact={(x['reading'],x['word'],x['meaning']):i+1 for i,x in enumerate(old)}
 aliases=[json.loads(s) for s in (D/'alias-candidates.jsonl').read_text(encoding='utf-8').splitlines()]
 compounds=[json.loads(s) for s in (D/'compound-candidates.jsonl').read_text(encoding='utf-8').splitlines()]
 edits=read(D/'compound-editorial.json');holds=[];reviews=[];entries=[];lines=[];kinds=collections.Counter()
 previous=[]
 for x in aliases:
  seed=x['seed'];assert byexact.get((seed['reading'],seed['word'],seed['meaning']))==seed['id'],'Stale alias seed'
  x=dict(x,kind='related-form',family='related-forms',genre='other')
  # A full form must not inherit the statement that its abbreviation is short.
  if x['word']!=seed['word']:
   x['meaning']=re.sub(r'[^。]*の\s*略。','',x['meaning']).strip()
  if not x['meaning'] or len(x['meaning'])<7:
   holds.append(dict(word=x['word'],reading=x['reading'],reason='別表記で循環説明になるため個別編集待ち。'));continue
  previous.append(x)
 for x in compounds:
  if x['word'] in edits['holdWords']:
   holds.append(dict(word=x['word'],reading=x['reading'],reason='接尾辞の直訳では語義を十分に説明できない。個別編集待ち。'));continue
  x=dict(x,kind='compound',family=x['rule'],genre='daily')
  if x['word'] in edits['overrides']:x['meaning']=edits['overrides'][x['word']];x['editorialOverride']=True
  if x['rule'].startswith(('権','料','代','費','者','員','業','事業')):x['genre']='society'
  if x['rule'].startswith(('辞典','用紙','研究','練習','訓練')):x['genre']='school'
  previous.append(x)
 # Recover the seed's exact genre. This does not infer identity from reading.
 idx=read(R/'data/shiritori-delivery/index.json');genres={}
 for chunk in idx['chunks']:
  for row in read(R/'data/shiritori-delivery'/chunk['file']):
   for i,w in enumerate(row['words']):genres[(row['reading'],w,row['meanings'][i])]=row['genres'][i]
 for x in previous:
  key=(x['reading'],x['word'])
  if key in pairs:continue
  if any(c in x['word']+x['meaning'] for c in ',\r\n\t'):raise ValueError('Unquoted CSV delimiter in '+x['word'])
  evidence=x.get('evidence') or [dict(entryId=x['entryId'],senseNumber=1)]
  url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&seq='+x['entryId']
  if x['kind']=='related-form':
   seed=x['seed'];x['genre']=genres[(seed['reading'],seed['word'],seed['meaning'])]
   meaningreason='読み・表記の適用先を守った単一名詞語義の別表記・関連語。説明は既存の語義から継承。'
   if x['relation']=='identical-single-sense-gloss-set':meaningreason+='別項目間は全英語語義集合の一致と、独立した日本語定義との一致を記録。'
   lexical=dict(method=x['relation'],entryId=x['entryId'],senseNumber=1,seedId=seed['id'],seedReading=seed['reading'],seedWord=seed['word'],trustedEditorialSeed=x['trustedEditorialSeed'],meaningChecks=x['meaningChecks'],equivalentGlossSet=seed.get('equivalentGlossSet',[]),seedEntryId=seed.get('seedEntryId'))
  else:
   meaningreason='独立した辞書見出し・名詞語義、構成語の品詞、複合語と構成語の英語語義の包含関係を確認。構造に基づく独自説明。'
   lexical=dict(method='dictionary-headword-stem-pos-and-gloss-composition',entryId=x['entryId'],evidence=evidence,stem=x['stem'],stemEvidence=x['stemEvidence'],rule=x['rule'],editorialOverride=x.get('editorialOverride',False))
  item=dict(id=len(old)+len(reviews)+1,reading=x['reading'],word=x['word'],meaning=x['meaning'],level=3,grade=4,category='一般語・複合語の関連展開',genre=x['genre'],kind=x['kind'],family=x['family'],
    lexicalSource=lexical,sources=[url],meaningReason=meaningreason,
    ageReason='一括照合による関連語候補として暫定レベル4。低学年・中学年への個別認定は行っていない。',
    distinctSenseReason='既存と同じ読みでも、出典の別表記・別名または別の語を保持する。既出判定は読み単位のまま。' if x['reading'] in oldread else '',
    imageReason='今回は語彙のみを追加。画像が適切な一般物は将来の画像補完候補。',imageEligible=True,image_mode='none',image_asset='',
    reviewStatus='source-checked-provisional',provisional=True)
  source=dict(title='JMdict / EDRDG・関連語の説明',url=url,license='CC BY-SA 4.0',verification=lexical['method'],reviewStatus='source-checked-provisional',jmdictIds=[x['entryId']])
  entries.append(dict(reading=x['reading'],word=x['word'],meaning=x['meaning'],genre=x['genre'],source=source))
  reviews.append(item);lines.append(','.join([x['reading'],x['word'],x['meaning'],'','3','','','none','']));pairs.add(key);kinds[x['kind']]+=1
 summary=dict(batch=BATCH,registered=False,baselineRows=len(old),baselineSha256=sha(before),added=len(reviews),
  newReadings=len({x['reading'] for x in reviews}-oldread),existingReadings=len({x['reading'] for x in reviews}&oldread),kinds=kinds,held=len(holds),
  grade=4,reviewStatus='source-checked-provisional',allIndividuallyReviewed=False,imagesGenerated=0)
 if not reviews:print(json.dumps(dict(added=0,exhaustedCurrentRules=True)));return
 save(BASE.with_suffix('.review.json'),reviews);save(BASE.with_suffix('.entries.json'),entries);save(BASE.with_suffix('.held.json'),holds);save(sf,summary)
 BASE.with_suffix('.csv').write_text('reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit\n'+'\n'.join(lines)+'\n',encoding='utf-8')
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 if '--apply' not in sys.argv:print(json.dumps(summary,ensure_ascii=False));return
 dfile=R/'data/shiritori-grade-decisions.json';d=read(dfile)
 assert d['sourceSha256']==sha(before) and d['reviewedRows']==len(old)
 assert read(R/'data/dictionary-imports/history.json')[-1]['afterSha256']==sha(before)
 assert (R/'whitelist.csv').read_bytes()==before,'Concurrent dictionary edit'
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(R/'whitelist.csv').read_bytes();assert after.startswith(before)
 if after==before:
  save(BASE.with_suffix('.review.json'),[]);save(BASE.with_suffix('.entries.json'),[])
  summary.update(added=0,exhaustedCurrentRules=True);save(sf,summary);print(json.dumps(summary,ensure_ascii=False));return
 finish_registration(summary,reviews,entries)
if __name__=='__main__':main()
