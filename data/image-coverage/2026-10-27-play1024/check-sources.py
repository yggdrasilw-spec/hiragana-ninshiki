import json,re,hashlib,urllib.request,urllib.parse,concurrent.futures,html
from pathlib import Path
HERE=Path(__file__).resolve().parent
urls=[
 'https://www.nintendo.com/jp/others/playing_cards/howtoplay/index.html',
 'https://45mix.net/koorioni/',
 'https://mattel.co.jp/toys/mattel_games/mattel_games-10961/',
 'https://www.takaratomy.co.jp/products/jinsei/',
 'https://catan.jp/',
 'https://www.super-sentai.net/',
 'https://www.tv-asahi.co.jp/50ger/',
 'https://www.shonenjump.com/j/rensai/',
 'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid=4999&request_locale=ja',
 'https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid=4007&request_locale=ja',
 'https://mtg-jp.com/products/card/3/',
 'https://mtg-jp.com/reading/translated/0034575/',
 'https://dm.takaratomy.co.jp/card/',
 'https://dm.takaratomy.co.jp/card/detail/?id=dm25rp2-TR03',
]
def get(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=35) as r:b=r.read();status=r.status;resolved=r.url
  s=b.decode('utf-8',errors='replace');title=re.search('<title[^>]*>(.*?)</title>',s,re.S)
  return dict(url=url,resolved=resolved,status=status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),title=html.unescape(re.sub('<[^>]+>','',title[1])).strip() if title else '')
 except Exception as e:return dict(url=url,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(get,urls))
riders=json.loads((HERE/'riders.json').read_text(encoding='utf-8'))
data=dict(checkedAt='2026-10-28',scope='ライダー全採用名は公式索引の実データに一致。ほかは代表資料を取得し名称・説明を編集確認。全項目の個別ページによる照合ではない。',sources=results,riderIndexes=[dict(url=x['url'],names=x['names'],links=x.get('links',[])) for x in riders if x['names']])
(HERE/'2026-10-27-play1024.sources.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(fetched=sum(x.get('status')==200 for x in results),total=len(results),unavailable=[x['url'] for x in results if 'error' in x]),ensure_ascii=False))
