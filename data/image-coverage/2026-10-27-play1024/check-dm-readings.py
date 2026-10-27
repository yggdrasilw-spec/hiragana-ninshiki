import json,urllib.request,urllib.parse,concurrent.futures,re,html
from pathlib import Path
H=Path(__file__).resolve().parent
items=json.loads((H/'2026-10-27-play1024.review.json').read_text(encoding='utf-8'))
names=list(dict.fromkeys(x['canonical'] for x in items if x['category']=='デュエル・マスターズのカード'))
def get(w):
 u='https://dmwiki.net/'+urllib.parse.quote('《'+w.replace('Ⅻ','XII')+'》')
 try:
  s=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25).read().decode('utf-8')
  heads=re.findall(r'<h2[^>]*>(.*?)</h2>',s,re.S)
  h=heads[0] if heads else ''
  return dict(word=w,url=u,heading=html.unescape(re.sub('<[^>]*>','',h)).strip(),ruby=[html.unescape(re.sub('<[^>]*>','',t)) for t in re.findall(r'<ruby[^>]*>(.*?)</ruby>',h,re.S)])
 except Exception as e:return dict(word=w,url=u,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:results=list(p.map(get,names))
(H/'dm-readings.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps([x for x in results if x.get('ruby')],ensure_ascii=False))
