"""Register the whole frozen scope, with explicit exclusions and source holds."""
import argparse,collections,csv,hashlib,io,json,re,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/vocabulary-gap/common4262'
BATCH='2026-11-16-common4262';BASE=R/'data/dictionary-imports'/BATCH
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def tsv(name):return {int(x['id']):x for x in csv.DictReader((D/name).open(encoding='utf-8'),delimiter='\t')}
def run(*args):subprocess.run(args,cwd=R,check=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');a=parser.parse_args()
 sf=BASE.with_suffix('.summary.json')
 if sf.exists() and read(sf).get('registered'):
  s=read(sf)
  current={(x['reading'],x['word'],x['meaning']) for x in csv.DictReader((R/'whitelist.csv').open(encoding='utf-8-sig'))}
  assert all((x['reading'],x['word'],x['meaning']) in current for x in read(BASE.with_suffix('.review.json')))
  if not s.get('deliveryBuilt'):
   run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');s['deliveryBuilt']=True;save(sf,s)
  print(json.dumps(dict(alreadyRegistered=True,**s),ensure_ascii=False));return
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 report=read(R/'data/vocabulary-gap/summary.json')
 assert sha(raw)==report['baselineSha256'],'Baseline changed: recheck all 4262 before registering'
 assert read(R/'data/dictionary-imports/history.json')[-1]['afterSha256']==sha(raw)
 scope=[json.loads(l) for l in (D/'scope.jsonl').open(encoding='utf-8')]
 drafts=[json.loads(l) for l in (D/'drafts.jsonl').open(encoding='utf-8')]
 assert len(scope)==len(drafts)==4262 and len({x['reading'] for x in scope})==4262
 supplements=read(D/'supplementary-sources.json')
 ed=tsv('editorial.tsv');ex=tsv('editorial-exclusions.tsv');holds=tsv('editorial-holds.tsv')
 assert len(ed)==len(list(csv.DictReader((D/'editorial.tsv').open(encoding='utf-8'),delimiter='\t'))),'Duplicate editorial IDs'
 assert not (set(ed)&set(ex) or set(ed)&set(holds) or set(ex)&set(holds))
 byreading={x['reading'] for x in old};reviews=[];entries=[];decisions=[];lines=[]
 allow_content_overrides={1758,1805,2418,3251,3638}
 for x in drafts:
  ident=x['id'];d=dict(scopeId=ident,reading=x['reading'],word=x['word'],endsWithN=x['endsWithN'])
  if ident in ex:d.update(status='excluded-content',reason=ex[ident]['reason'])
  elif ident in holds:d.update(status='held-source-meaning',reason=holds[ident]['reason'])
  elif x['status']=='excluded-content' and ident not in allow_content_overrides:
   d.update(status='excluded-content',reason=x['reason'])
  else:
   edited=ident in ed;meaning=ed[ident]['meaning'] if edited else x.get('meaning')
   assert meaning and (edited or x['status']=='draft-source-definition'),f'Unresolved: {ident}'
   assert not re.search('[,\t\r\n<>]',x['word']+meaning),ident
   assert x['reading'] not in byreading,'Scope reading already exists; update review first'
   assert re.fullmatch('[ぁ-ゖー]+',x['reading'])
   extra=supplements.get(str(ident),[])
   primary=(extra[0] if extra else x['evidence'][0]['url']) if edited else x['sourceUrl']
   lexical=dict(method='applicable-jmdict-form-reading-and-editorial-definition' if edited else 'applicable-jmdict-form-reading-and-japanese-dictionary-definition',
    jmdict=x['evidence'],japaneseDefinitionSource=None if edited else dict(word=x['sourceWord'],sense=x['sourceSense'],
    url=x['sourceUrl'],originalDefinition=x['originalDefinition'],readingForms=x['readingForms'],aliasTrail=x['aliasTrail']))
   review=dict(id=len(old)+len(reviews)+1,scopeId=ident,reading=x['reading'],word=x['word'],meaning=meaning,
    level=3,grade=4,category='一般的な読み4262・全件確認',genre='other',lexicalSource=lexical,
    meaningReason='出典の適用する表記・読み・名詞語義を保存。'+('英語原文や日本語資料を参照して説明を個別編集。' if edited else '日本語版Wiktionaryの該当見出しの定義を使用。句読点・空白を整形。読み違い・参照のみの定義を除外し、曖昧な箇所は個別編集。'),
    ageReason='学年適合性の個別認定は未完。出典照合を行った発展語彙として暫定レベル4に置き、低学年CPUには自動追加しない。',
    imageReason='今回は説明のみを追加。一般物の画像は将来の補完候補として保持。',imageEligible=True,image_mode='none',image_asset='',
    reviewStatus='source-checked-provisional',provisional=True,definitionIndividuallyEdited=edited,
    sources=list(dict.fromkeys([primary]+extra+[e['url'] for e in x['evidence']])),endsWithN=x['endsWithN'])
   source=dict(title='JMdict / 独自編集の説明' if edited else '日本語版Wiktionaryの執筆者 / JMdict',url=primary,
    license='CC BY-SA 4.0',verification=lexical['method'],reviewStatus='source-checked-provisional',
    jmdictIds=[e['entryId'] for e in x['evidence']],definitionAuthor='独自編集' if edited else '日本語版Wiktionaryの執筆者',
    attributionNotice='data/vocabulary-gap/common4262/NOTICE.md')
   reviews.append(review);entries.append(dict(reading=x['reading'],word=x['word'],meaning=meaning,genre='other',source=source))
   lines.append(','.join([x['reading'],x['word'],meaning,'','3','','','none','']))
   d.update(status='approved-source-provisional',meaning=meaning,definitionIndividuallyEdited=edited,
    reason='日本語説明・出典・語形・読み・内容の確認を記録。個別の小学校学年認定は未完。',reviewId=review['id'])
  decisions.append(d)
 assert len(decisions)==4262 and len({x['reading'] for x in reviews})==len(reviews)
 (D/'decisions.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in decisions),encoding='utf-8')
 header=raw.decode('utf-8-sig').splitlines()[0]
 BASE.with_suffix('.csv').write_text(header+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')
 save(BASE.with_suffix('.review.json'),reviews);save(BASE.with_suffix('.entries.json'),entries)
 save(BASE.with_suffix('.excluded.json'),[x for x in decisions if x['status']!='approved-source-provisional'])
 s=dict(batch=BATCH,registered=False,baselineSha256=sha(raw),baselineRows=len(old),baselineReadings=len(byreading),
   scopeReadings=4262,added=len(reviews),newReadings=len(reviews),statuses=dict(collections.Counter(x['status'] for x in decisions)),
   individuallyEdited=sum(x['definitionIndividuallyEdited'] for x in reviews),inheritedJapaneseDefinitions=sum(not x['definitionIndividuallyEdited'] for x in reviews),
   endingN=sum(x['endsWithN'] for x in reviews),grade=4,allIndividuallyReviewed=False,expertReviewed=False,imagesGenerated=0,
   scopeSha256=sha((D/'scope.jsonl').read_bytes()),decisionsSha256=sha((D/'decisions.jsonl').read_bytes()))
 save(sf,s)
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 if not a.apply:print(json.dumps(s,ensure_ascii=False));return
 grades=read(R/'data/shiritori-grade-decisions.json')
 assert grades['sourceSha256']==sha(raw) and grades['reviewedRows']==len(old)
 assert (R/'whitelist.csv').read_bytes()==raw
 run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(R/'whitelist.csv').read_bytes();assert after.startswith(raw)
 history=read(R/'data/dictionary-imports/history.json')[-1]
 assert len(history['addedLines'])==len(reviews),'Import filtered a retired item: reconcile before finishing'
 assert history['afterSha256']==sha(after)
 for x in reviews:grades['levels']['4']+=' '+str(x['id']-1)
 grades.update(sourceSha256=sha(after),reviewedRows=len(old)+len(reviews));save(R/'data/shiritori-grade-decisions.json',grades)
 s.update(registered=True,afterSha256=sha(after),totalRows=len(old)+len(reviews),totalReadings=len(byreading)+len(reviews));save(sf,s)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
 s['deliveryBuilt']=True;save(sf,s);print(json.dumps(s,ensure_ascii=False))

if __name__=='__main__':main()
