import urllib.request,re,json,html,concurrent.futures
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def get(page):
 u=f'https://www.kamen-rider-official.com/zukan/kamen_rider_members?sort_column=kana_name&page={page}'
 try:
  b=urllib.request.urlopen(u,timeout=30).read();s=b.decode('utf-8')
  names=re.findall(r'<p class="p-Card__textbox[^>]*>(.*?)</p>',s)
  links=re.findall(r'href="(/zukan/kamen_rider_members/\d+)"',s)
  return {'url':u,'names':[html.unescape(re.sub('<[^>]*>','',n)) for n in names],'links':links}
 except Exception as e:return {'url':u,'error':str(e),'names':[]}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:rows=list(p.map(get,range(1,31)))
(ROOT/'riders.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([(i+1,len(x['names'])) for i,x in enumerate(rows)]))
print(json.dumps([x for r in rows[:2] for x in r['names']],ensure_ascii=False))
