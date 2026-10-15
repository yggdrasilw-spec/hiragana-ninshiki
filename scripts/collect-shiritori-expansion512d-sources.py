"""Read public lexical references; never retrieve images or republish articles."""
import hashlib,json,urllib.parse,urllib.request,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/image-coverage/2026-10-15-expansion512d'
CACHE=Path('C:/Users/user/.cache/shiritori-qa/expansion512d-sources')
items=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))['items']
words=[x['word'] for x in items if not x['category'].startswith('選手:')]
def collect(titles):
 params=dict(action='query',format='json',prop='info',inprop='url',exintro=1,explaintext=1,exchars=600,redirects=1,titles='|'.join(titles))
 url='https://ja.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params)
 cache=CACHE/('wiki-'+hashlib.sha256('|'.join(titles).encode()).hexdigest()[:12]+'.json')
 if cache.exists():data=json.loads(cache.read_text(encoding='utf-8'))
 else:
  for attempt in range(4):
   try:
    data=json.load(urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Shiritori vocabulary evidence/1.0'}),timeout=30));break
   except urllib.error.HTTPError as e:
    if e.code!=429 or attempt==3:raise
    time.sleep(15)
  time.sleep(2)
 (CACHE/('wiki-'+hashlib.sha256('|'.join(titles).encode()).hexdigest()[:12]+'.json')).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
 q=data['query'];redirects={r['from']:r['to'] for r in q.get('normalized',[])+q.get('redirects',[])};pages={r['title']:r for r in q['pages'].values() if 'missing' not in r}
 result=[]
 for word in titles:
  title=word
  for _ in range(8):
   if title not in redirects:break
   title=redirects[title]
  page=pages.get(title)
  result.append(dict(word=word,matched=bool(page),**({k:page[k] for k in ['title','pageid','lastrevid','fullurl']} if page else {})))
 return result
results=[]
with ThreadPoolExecutor(max_workers=1) as pool:
 for group in pool.map(collect,[words[i:i+35] for i in range(0,len(words),35)]):results+=group
(OUT/'lexical-crosscheck.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checked=len(results),matched=sum(x['matched'] for x in results),unmatched=[x['word'] for x in results if not x['matched']]),ensure_ascii=False))
