import json,urllib.request,urllib.parse,re,html,concurrent.futures
from pathlib import Path
H=Path(__file__).resolve().parent;B=H/'2026-10-27-play1024'
a=json.loads(B.with_suffix('.review.json').read_text(encoding='utf-8'));names=list(dict.fromkeys(x['canonical'] for x in a if x['category']=='遊戯王のカード'))
def get(w):
 u='https://www.db.yugioh-card.com/yugiohdb/card_search.action?'+urllib.parse.urlencode(dict(ope=1,keyword=w,stype=1,request_locale='ja',rp=10))
 try:
  s=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read().decode('utf-8')
  # The publisher keeps phonetic card names separate from printed names.
  entries=[]
  for fragment in re.findall(r'<div[^>]*class="[^\"]*box_card_name[^\"]*"[^>]*>(.*?)</div>',s,re.S):
   entries.append(html.unescape(re.sub('<[^>]*>',' ',fragment)).strip())
  return dict(word=w,url=u,entries=[' '.join(x.split()) for x in entries])
 except Exception as e:return dict(word=w,url=u,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as p:results=list(p.map(get,names))
(H/'yugioh-name-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(checked=len(results),withEntries=sum(bool(x.get('entries')) for x in results),examples=results[:3]),ensure_ascii=False))
