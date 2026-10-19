"""Archive authoritative taxonomic evidence without changing vocabulary."""
import json,urllib.request,concurrent.futures,hashlib,re,html,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512';D=O/'sources';D.mkdir(exist_ok=True)
p=json.loads((O/'plan.json').read_text(encoding='utf-8'))
jobs={}
for x in p['items']:
 s=x.get('scientificName','')
 if x['category']=='reptiles':
  g,sp=s.split()[:2];jobs[s]=f'https://reptile-database.reptarium.cz/{g}/{sp}'
for label,url in json.loads((O/'sources.json').read_text(encoding='utf-8')).items():
 if label in ['elements','angels','demons','gems','minerals','frogs','accessories']:jobs[label]=url
def fetch(job):
 label,url=job;dest=D/(re.sub('[^a-zA-Z0-9-]','-',label)+'.html')
 try:
  if dest.exists():raw=dest.read_bytes()
  else:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (educational vocabulary review)'})
   with urllib.request.urlopen(req,timeout=45) as r:raw=r.read()
   dest.write_bytes(raw)
  text=html.unescape(re.sub('<[^>]+>',' ',raw.decode('utf-8',errors='replace')))
  return dict(label=label,url=url,path=dest.relative_to(R).as_posix(),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),nameFound=label in text if ' ' in label else True,title=re.sub(r'\s+',' ',text).strip()[:160],status='retrieved')
 except Exception as e:return dict(label=label,url=url,status='failed',error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:result=list(ex.map(fetch,jobs.items()))
(O/'research.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(total=len(result),retrieved=sum(x['status']=='retrieved' for x in result),failed=[x['label'] for x in result if x['status']!='retrieved']),ensure_ascii=False))
