"""Archive source availability and distinguish editorial review from literal matches."""
import concurrent.futures,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-16-expansion1024f'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items']
extra=['https://la28.org/en/games-plan/olympics.html','https://support.olympics.com/hc/en-gb/articles/43002667811219-What-sports-are-in-the-Olympic-Winter-Games-Milano-Cortina-2026','https://www.joc.or.jp/sports/pentathlon/index.html','https://www.atrion-s.com/products/page/1','https://www.lotte.co.jp/products/','https://www.koikeya.co.jp/','https://www.sanko-seika.co.jp/','https://www.tohato.jp/products/','https://www.yamazaki-biscuits.co.jp/products/','https://www.orionstar.co.jp/','https://www.kracie.co.jp/foods/okashi/','https://www.yurakuseika.co.jp/lineup/']
urls=sorted({u for x in items for u in x['sources']}|set(extra));folder=OUT/'sources';folder.mkdir(exist_ok=True)
def fetch(url):
 filename=hashlib.sha256(url.encode()).hexdigest()[:16]+'.html';p=folder/filename
 try:
  if not p.exists():
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (educational vocabulary source audit)'})
   with urllib.request.urlopen(req,timeout=25) as r:body=r.read();status=r.status
   p.write_bytes(body)
  body=p.read_bytes()
  return dict(url=url,available=True,file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
 except Exception as e:return dict(url=url,available=False,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:sources=list(ex.map(fetch,urls))
texts={s['url']:(ROOT/s['file']).read_bytes().decode('utf-8','replace') for s in sources if s['available']}
records=[]
for x in items:
 matches=[url for url,text in texts.items() if x['word'] in text]
 records.append(dict(slot=x['slot'],word=x['word'],category=x['category'],authoredDefinition=x['meaning'],sources=x['sources'],literalHeadingMatches=matches,reviewMethod='独自編集。公式一覧の文字列一致は補助証拠であり、全語の個別実証や画像の利用許諾を意味しない。',**({'correction':'明治から移管後のメーカーはアトリオン製菓。','verifiedURL':'https://www.atrion-s.com/products/page/1'} if x['word'] in ['ヨーグレット','ハイレモン'] else {})))
audit=dict(retrievedAt=datetime.now(timezone.utc).isoformat(),sources=sources,rows=records,scope='名称・分類・ルールを参照。説明文は転載せず独自に作成。商品写真・ロゴ・既存の妖怪キャラクター画は取り込まない。')
(OUT/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(sources=len(sources),available=sum(x['available'] for x in sources),literalMatches=sum(bool(x['literalHeadingMatches']) for x in records),entries=len(records)),ensure_ascii=False))
