"""Collect bounded lexical index evidence; presence does not validate meaning."""
import concurrent.futures,hashlib,json,re,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-27-game512'
items=json.loads(BASE.with_suffix('.review.json').read_text(encoding='utf-8'))
urls=['https://wikiwiki.jp/dqdic3rd/呪文']+['https://wikiwiki.jp/ffdic/魔法/'+x+'行' for x in 'あかさたなはまやらわ']+[
 'https://jp.finalfantasyxiv.com/jobguide/blackmage/','https://jp.finalfantasyxiv.com/jobguide/whitemage/','https://jp.finalfantasyxiv.com/jobguide/redmage/',
 'https://www.nintendo.com/jp/games/feature/nintendo-classics/index.html',
 'https://www.dragonquest.jp/products/','https://www.jp.square-enix.com/game/','https://wiki.ffo.jp/html/24125.html']
def fetch(url):
 try:
  req=urllib.request.Request(urllib.parse.quote(url,safe=':/?=&'),headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=25) as r:blob=r.read();status=r.status
  return dict(url=url,status=status,sha256=hashlib.sha256(blob).hexdigest(),bytes=len(blob)),blob.decode('utf-8',errors='replace')
 except Exception as e:return dict(url=url,error=str(e)),''
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,urls))
checks=[]
for x in items:
 if x['source'] not in ('dq-spells','ff-spells'):continue
 sources=[meta['url'] for meta,body in results if x['word'] in body and (('dqdic3rd' in meta['url']) if x['source']=='dq-spells' else ('ffdic' in meta['url'] or 'finalfantasyxiv.com' in meta['url'] or 'wiki.ffo.jp' in meta['url']))]
 checks.append(dict(word=x['word'],reading=x['reading'],nameFound=bool(sources),sources=sources))
 x['lexicalSource']['lookupEvidence']=checks[-1]
BASE.with_suffix('.review.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
result=dict(checkedAt='2026-10-27',method='取得した索引や公式ジョブガイドの文字列照合。名称の存在のみを確認し効果や子どもへの適切さは編集確認。ゲーム全タイトルと略称の個別ページ取得は未実施。',sources=[m for m,b in results],spellChecks=checks)
BASE.with_suffix('.sources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(fetched=sum(bool(b) for m,b in results),spellNames=len(checks),matched=sum(x['nameFound'] for x in checks),unmatched=[x['word'] for x in checks if not x['nameFound']]),ensure_ascii=False))
