import requests,json,time,concurrent.futures,sys,threading
from pathlib import Path
ROOT=Path(r'C:\Users\user\hiragana-ninshiki')
OUT=ROOT/'data/dictionary-imports/art-history-sources';OUT.mkdir(exist_ok=True)
API='https://ja.wikipedia.org/w/api.php'
HEAD={'User-Agent':'ArtVocabularyEducationalBot/1.0 (educational vocabulary research)','Accept':'application/json'}
LOCK=threading.Lock()
lastRequest=0
def get(p):
 global lastRequest
 for attempt in range(3):
  try:
   with LOCK:
    time.sleep(max(0,1.1-(time.monotonic()-lastRequest)));lastRequest=time.monotonic()
   r=requests.get(API,params={'action':'query','format':'json',**p},headers=HEAD,timeout=25);r.raise_for_status();r.encoding='utf8';d=r.json()
   if 'error' in d:raise ValueError(d['error'])
   return d
  except Exception as error:
   print('retry',attempt,str(error)[:200],flush=True)
   if attempt==2:raise
   time.sleep(10+attempt*8)
def category(t):
 p={'list':'categorymembers','cmtitle':t,'cmlimit':500};items=[]
 while True:
  d=get(p);items+=d['query']['categorymembers']
  if 'continue' not in d:break
  p.update(d['continue'])
 return t,items
groups=[('流派・美術史',['美術史','芸術運動','美術のジャンル'],1),('技法・画材',['美術の技法','画材','色','色名','版画','絵画技術','絵画のジャンル','版画技法','日本画'],1),('工芸・装飾',['美術工芸','装飾','陶芸','漆芸','書','彫刻','仏像'],0),('絵画作品',['浮世絵作品','日本の絵画','絵巻物'],0),('彫刻作品',['彫刻作品','古代ギリシアの彫刻','ロダンの彫刻作品'],0)]
skip=['人物','画家','彫刻家','芸術家','評論家','美術家','写真家','学者','美術館','博物館','一覧','賞','団体','企業','学校','大学','画廊','映画','漫画','小説','雑誌','書籍','スタブ','テンプレート','所蔵','画像','イベント','展覧会','教育','年の','世紀生','生年','没年','作家','による作品','アニメ','ゲーム']
cachefile=OUT/'categories.json';cache=json.loads(cachefile.read_text(encoding='utf8')) if cachefile.exists() else {}
pages={}
for group,roots,depth in groups:
 frontier=['Category:'+t for t in roots];visited=set()
 for level in range((0 if group=='技法・画材' else depth)+1):
  todo=[t for t in frontier if t not in visited];visited.update(todo);frontier=[]
  missing=[t for t in todo if t not in cache]
  if group=='流派・美術史' and level==1:todo=[t for t in todo if t in cache];missing=[]
  with concurrent.futures.ThreadPoolExecutor(1) as pool:
   for t,items in pool.map(category,missing):
    cache[t]=items
    cachefile.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf8')
    print('category',t,len(items),flush=True)
    time.sleep(1)
  cachefile.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf8')
  for t in todo:
   for x in cache[t]:
    title=x['title']
    if x['ns']==0 and not any(w in title for w in ['一覧','Template:']):pages.setdefault(x['pageid'],dict(**x,group=group,category=t))
    elif x['ns']==14 and not any(w in title for w in skip):frontier.append(title)
  print(group,level,len(todo),len(pages),flush=True)
paintings=json.loads((OUT/'wikidata-paintings-partial.json').read_text(encoding='utf8'))['rows']
titles={x['title'] for x in pages.values()}
extra=[x['label']['value'] for x in paintings if x['label']['value'] not in titles]
ess=[x.split('\t')[0] for x in (OUT/'essentials.tsv').read_text(encoding='utf8').splitlines()]
extra=list(dict.fromkeys(ess+extra))
resolvedfile=OUT/'resolved.json';resolved=json.loads(resolvedfile.read_text(encoding='utf8')) if resolvedfile.exists() else {}
for k,x in resolved.items():pages.setdefault(int(k),x)
already={x['title'] for x in resolved.values()};extra=[t for t in extra if t not in already]
def resolve(titles):return get({'titles':'|'.join(titles),'redirects':1})['query']['pages']
with concurrent.futures.ThreadPoolExecutor(1) as pool:
 for n,found in enumerate(pool.map(resolve,[extra[i:i+20] for i in range(0,len(extra),20)])):
  for k,x in found.items():
   if int(k)>0:
    v=dict(pageid=int(k),ns=0,title=x['title'],group='絵画作品',category='Wikidata絵画・重点語');pages.setdefault(int(k),v);resolved[k]=v
  resolvedfile.write_text(json.dumps(resolved,ensure_ascii=False),encoding='utf8')
  if n%10==0:print('resolved',n,len(pages),flush=True)
(OUT/'pages.json').write_text(json.dumps(list(pages.values()),ensure_ascii=False,indent=2),encoding='utf8')
extractfile=OUT/'extracts.json';extracts=json.loads(extractfile.read_text(encoding='utf8')) if extractfile.exists() else {}
ids=[str(i) for i in pages if str(i) not in extracts]
def extract(ids):
 d=get({'prop':'extracts|revisions|pageprops','pageids':'|'.join(ids),'exintro':1,'explaintext':1,'rvprop':'ids|timestamp','ppprop':'wikibase_item','exlimit':20})
 return d['query']['pages']
with concurrent.futures.ThreadPoolExecutor(1) as pool:
 for n,result in enumerate(pool.map(extract,[ids[i:i+20] for i in range(0,len(ids),20)])):
  for value in result.values():value['extract']=value.get('extract','').split('\n')[0][:4000]
  extracts.update(result)
  if True:
   extractfile.write_text(json.dumps(extracts,ensure_ascii=False),encoding='utf8');print('extracts',len(extracts),flush=True)
extractfile.write_text(json.dumps(extracts,ensure_ascii=False),encoding='utf8')
print('DONE',len(extracts))
