"""Prepare/review the 512 mythological meanings, then import with --import-reviewed.

The nine-column CSV keeps compatibility level 3; the meaning-specific runtime
policy explicitly assigns grade 5. No old meaning is rewritten or reclassified.
"""
import argparse,collections,csv,hashlib,importlib.util,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-19-mythology512'
QA=ROOT/'qa-output/mythology512-research'
spec=importlib.util.spec_from_file_location('research',ROOT/'scripts/research-shiritori-mythology512.py')
research=importlib.util.module_from_spec(spec);spec.loader.exec_module(research)
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
run=lambda *a:subprocess.run(a,cwd=ROOT,check=True)

EXISTING={'神産巣日神','火之迦具土神','思金神','邇邇芸命'}
RESERVE={'クレイオス','コイオス','ポイベ','テイア','ヒュペリオン','アイテル','ヘメラ',
         'アンティゴネ','カドモス','プシュケ','宇摩志阿斯訶備比古遅神','天之常立神',
         '国之常立神','豊雲野神','速秋津比古神','速秋津比売神','鳥之石楠船神',
         'スリュムヘイム','レーヴァテイン','プーシャン'}

def meaning(item):
 group=item['group'];detail=item['detail']
 if group=='イラン' and detail.startswith('ゾロアスター教'):return 'イランの'+detail
 if group=='フィンランド' and detail.startswith('叙事詩'):return 'フィンランドの'+detail
 return group+'神話で、'+detail

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--import-reviewed',action='store_true');args=parser.parse_args()
 summaryfile=BASE.with_suffix('.summary.json')
 if summaryfile.exists():
  summary=json.loads(summaryfile.read_text(encoding='utf-8'))
  if summary.get('registered'):
   rows=list(csv.DictReader((ROOT/'whitelist.csv').read_text(encoding='utf-8').splitlines()))
   reviews=json.loads(BASE.with_suffix('.review.json').read_text(encoding='utf-8'))
   assert all(all(rows[x['id']-1][k]==x[k] for k in ('reading','word','meaning')) for x in reviews)
   print(json.dumps(dict(alreadyRegistered=True,meanings=len(reviews))));return
 before=(ROOT/'whitelist.csv').read_bytes()
 old=list(csv.DictReader(before.decode('utf-8').splitlines()))
 decisionsfile=ROOT/'data/shiritori-grade-decisions.json'
 decisions=json.loads(decisionsfile.read_text(encoding='utf-8'))
 assert decisions['sourceSha256']==sha(before) and decisions['reviewedRows']==len(old)
 sources=json.loads(BASE.with_suffix('.sources.json').read_text(encoding='utf-8'))
 evidence={x['word']:x for x in json.loads((QA/'evidence.json').read_text(encoding='utf-8'))}
 candidates=list(research.candidates());items=[];excluded=[]
 for x in candidates:
  if x['word'] in EXISTING|RESERVE:
   excluded.append(dict(**x,reason='同じ神・同じ意味が登録済み' if x['word'] in EXISTING else '初回512件の対象外として保留。別名での水増しや不確かな武器の断定を避ける。'))
   continue
  assert re.fullmatch('[ぁ-ゖー]+',x['reading']),x
  assert not any(x['word']==r['word'] and x['reading']==r['reading'] and ('神' in r['meaning'] or '神話' in r['meaning']) for r in old),x
  text=meaning(x);matches=[r for r in old if r['reading']==x['reading']]
  e=evidence[x['word']]
  naming={k:e[k] for k in ('title','url','missing','disambiguation')}
  lexical=dict(tradition=x['group'],sources=sources['traditions'][x['group']],consultedAt='2026-10-19')
  specific={
   'ピナーカ':dict(title='University of Chicago: Meghanadavadha glossary, Pinaka',url='https://home.uchicago.edu/~cbs2/Meghanada.pdf.files/glossary_Megha.pdf'),
   'オショシ':dict(title='MASP: Oshosi Hunting',url='https://masp.org.br/en/collections/works/oshosi-hunting'),
   '藍采和':dict(title='平凡社 世界大百科事典: 藍采和（読み らんさいわ）',url='https://kotobank.jp/word/藍采和-1435179'),
  }
  if x['word'] in specific:lexical['specificReference']=specific[x['word']]
  if not e['missing'] and not e['disambiguation']:
   lexical['japaneseNameReference']=dict(title=e['title'],url=e['url'])
  en=e.get('englishEvidence')
  if en and not en['missing'] and not en['disambiguation']:
   lexical['englishReference']=dict(title=en['title'],url=en['url'])
   naming['englishReference']=dict(title=en['title'],url=en['url'])
  item=dict(**{k:x[k] for k in ('reading','word','kind')},tradition=x['group'],meaning=text,
            id=len(old)+len(items)+1,grade=5,level=3,imagequery=x['word'],imagequery_en='',image_asset='',image_mode='none',image_credit='',
            lexicalSource=lexical,namingEvidence=naming,
            meaningReason='体系と役割を限定した独自の短い説明。伝承の異同を一般化せず、ゲーム作品独自の設定は含めない。',
            ageReason='神話の個別固有名を扱う知識として、利用者指定のレベル5に配置。既存の同音異義語のレベルは維持。',
            imageReason='図像は未制作。今回は名称と説明を先に登録し、説明のみの表示で無関係な外部画像を検索しない。')
  if matches:item['distinctSenseReason']='既存の'+ '／'.join(r['word']+'：'+r['meaning'] for r in matches)+'とは別の、'+x['group']+'神話の固有名。読みが同じでも語義を分離する。'
  items.append(item)
 assert len(items)==512 and len({x['reading'] for x in items})==512
 assert len({(x['reading'],x['word'],x['meaning']) for x in items})==512
 assert len(excluded)==24
 fields='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
 batch=BASE.with_suffix('.csv')
 for x in items:assert all(',' not in str(x[k]) and '\n' not in str(x[k]) for k in fields)
 with batch.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(items)
 save(BASE.with_suffix('.review.json'),items);save(BASE.with_suffix('.excluded.json'),excluded)
 summary=dict(date='2026-10-19',registered=False,addedMeanings=512,newReadings=sum(not any(r['reading']==x['reading'] for r in old) for x in items),
              homonymousReadings=sum(any(r['reading']==x['reading'] for r in old) for x in items),
              endingN=sum(x['reading'].endswith('ん') for x in items),grade=5,explanationOnly=512,
              baselineRows=len(old),beforeSha256=sha(before),traditions=dict(collections.Counter(x['tradition'] for x in items)),
              kinds=dict(collections.Counter(x['kind'] for x in items)),excludedExisting=4,reserved=20)
 save(summaryfile,summary)
 run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
 if not args.import_reviewed:print(json.dumps(summary,ensure_ascii=False));return
 # Refuse to import if another batch changed shared files after review.
 assert (ROOT/'whitelist.csv').read_bytes()==before
 assert json.loads(decisionsfile.read_text(encoding='utf-8'))==decisions
 baseline=QA/'registration-baseline.csv'
 if baseline.exists():assert baseline.read_bytes()==before
 else:baseline.write_bytes(before)
 run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
 after=(ROOT/'whitelist.csv').read_bytes()
 assert after.startswith(before) and len(after.decode('utf-8').splitlines())-1==len(old)+512
 decisions['levels']['5']+=' '+str(len(old))+'-'+str(len(old)+511)
 for x in items:decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
 decisions.update(sourceSha256=sha(after),reviewedRows=len(old)+512)
 save(decisionsfile,decisions)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
 coveragefile=ROOT/'data/image-coverage/review-2026-10-10.json'
 coverage=json.loads(coveragefile.read_text(encoding='utf-8'));assert len(coverage)==len(old)
 for x in items:
  coverage.append(dict(id=x['id'],**{k:str(x[k]) for k in ('reading','word','meaning','level','image_asset')},
                       category='mythology',target=True,scopeReason='世界の神話体系の固有名を追加。画像は未制作で説明のみ。',
                       status='explanation-only',assignment='none',originalId=None))
 save(coveragefile,coverage)
 # There are no image mutations: append text dates and preserve every image
 # fingerprint and all prior update dates without scanning R2 originals.
 updatesfile=ROOT/'data/image-coverage/review-updates.json'
 updates=json.loads(updatesfile.read_text(encoding='utf-8'))
 assert updates['csvSha256']==sha(before) and len(updates['entries'])==len(old)
 from datetime import datetime,timezone
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 for x in items:
  updates['entries'].append(dict(id=x['id'],text=[x[k] for k in ('reading','word','meaning')],
       textUpdatedAt=now,image_asset='',imageAssignedAt=''))
 updates['csvSha256']=sha(after);updates.pop('revision',None)
 updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 updatesfile.write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 summary.update(registered=True,afterSha256=sha(after),totalRows=len(old)+512)
 save(summaryfile,summary)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
