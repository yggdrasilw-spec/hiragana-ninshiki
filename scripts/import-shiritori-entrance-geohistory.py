"""Register the curated entrance-level corpus, preserving the existing import gate.

Dry-run by default. --write validates, imports, synchronizes ledgers and builds delivery.
"""
import collections,csv,hashlib,io,json,re,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/entrance-geohistory'
BASE=ROOT/'data/dictionary-imports/2026-10-28-entrance-geohistory'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
def main():
 summaryPath=BASE.with_suffix('.summary.json')
 if summaryPath.exists() and read(summaryPath).get('registered'):
  if '--write' in sys.argv:run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-entrance-catalog.py')
  print(json.dumps({'alreadyRegistered':True,'added':read(summaryPath)['added']}));return
 baseline=read(CAT/'preparation.json')
 before=(ROOT/'whitelist.csv').read_bytes()
 assert sha(before)==baseline['beforeSha256'],'Dictionary changed: rebuild preparation before importing'
 old=list(csv.DictReader(io.StringIO(before.decode('utf-8'))))
 corpus=[json.loads(l) for l in (CAT/'entries.jsonl').read_text(encoding='utf-8').splitlines()]
 assert len({x['catalogId'] for x in corpus})==len(corpus)
 sources=read(CAT/'sources.json')
 additions=[]
 for x in corpus:
  assert re.fullmatch('[ぁ-ゖー]+',x['reading'])
  if x['status']!='add':continue
  assert not any(y['word']==x['word'] for y in old),x['word']
  subject=x['topics'][0].split('/')[0]
  evidence=dict(method='標準用語として編集選定。科目資料は学習範囲の根拠であり全語の個別照合を意味しない。',references=sources['scopeReferences'][subject],reviewedOn='2026-10-28')
  if x['dictionaryEntries']:evidence.update(dictionary='JMdict',entries=x['dictionaryEntries'],word=x['word'],reading=x['reading'])
  if x['word']=='受領':evidence.update(specificReference='https://kotobank.jp/word/受領-85239',note='一般語のじゅりょうとは別に歴史用語のずりょうを確認')
  row=dict(id=len(old)+len(additions)+1,reading=x['reading'],word=x['word'],meaning=x['meaning'],imagequery=x['word'],level='3',imagequery_en='',image_asset='',image_mode='none',image_credit='',grade=5,category=subject,topics=x['topics'],catalogId=x['catalogId'],lexicalSource=evidence,meaningReason='時代・地域・制度などの文脈を短い独自説明で示す。'+x['meaning'],ageReason='高校の'+subject+'の専門語義として意味別レベル5に配置。',imageReason='今回は説明のみ。画像や外部画像検索を使わない。')
  hom=[y for y in old if y['reading']==x['reading']]
  if hom:row['distinctSenseReason']='同じ読みの既存語（'+'／'.join(y['word'] for y in hom)+'）から専門語義を区別する。'+x['meaning']
  additions.append(row)
 assert len(additions)==baseline['status']['add']
 header=before.decode('utf-8').splitlines()[0].split(',')
 out=io.StringIO();writer=csv.DictWriter(out,fieldnames=header,extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(additions)
 for row in additions:
  assert not any(c in row[k] for k in header for c in ',\r\n'),row['word']
 summary=dict(registered=False,baselineRows=len(old),beforeSha256=sha(before),added=len(additions),categories=dict(collections.Counter(x['category'] for x in additions)),newReadings=len({x['reading'] for x in additions}-{x['reading'] for x in old}),endingN=sum(x['reading'].endswith('ん') for x in additions),explanationOnly=len(additions),catalogCandidates=len(corpus),existingForms=baseline['status']['existing-form'])
 if '--write' not in sys.argv:print(json.dumps(summary,ensure_ascii=False));return
 dfile=ROOT/'data/shiritori-grade-decisions.json';d=read(dfile)
 cfile=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(cfile)
 ufile=ROOT/'data/image-coverage/review-updates.json';updates=read(ufile)
 assert d['sourceSha256']==sha(before) and d['reviewedRows']==len(old)
 assert len(coverage)==len(old) and updates['csvSha256']==sha(before) and len(updates['entries'])==len(old)
 BASE.with_suffix('.csv').write_text(out.getvalue(),encoding='utf-8',newline='\n')
 save(BASE.with_suffix('.review.json'),additions)
 save(BASE.with_suffix('.sources.json'),sources)
 save(summaryPath,summary)
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 assert (ROOT/'whitelist.csv').read_bytes()==before
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(ROOT/'whitelist.csv').read_bytes();assert after==before+out.getvalue().split('\n',1)[1].encode('utf-8'),'Existing bytes or appended rows differ'
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 for x in additions:
  d['levels']['5']+=' '+str(x['id']-1);d.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
  coverage.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],level='3',image_asset='',category=x['category'],target=True,scopeReason='大学受験を視野に地理歴史の専門語を追加。',status='explanation-only',assignment='none',originalId=None))
  updates['entries'].append(dict(id=x['id'],text=[x['reading'],x['word'],x['meaning']],textUpdatedAt=now,image_asset='',imageAssignedAt=''))
 d.update(sourceSha256=sha(after),reviewedRows=len(old)+len(additions));save(dfile,d)
 save(cfile,coverage)
 updates['csvSha256']=sha(after);updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 ufile.write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
 summary.update(registered=True,afterSha256=sha(after),totalRows=len(old)+len(additions));save(summaryPath,summary)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-entrance-catalog.py')
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
