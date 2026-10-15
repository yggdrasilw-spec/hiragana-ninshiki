"""Add the user's requested expanded spellings without shifting prepared image IDs."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c'
p=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
d=json.loads((OUT/'draft.json').read_text(encoding='utf-8'))
groups={'きゃらくたーめいく':'キャラメイク','ぷろふぃーるちょう':'プロフ帳','ぬいぐるみふく':'ぬい服','ぬいぐるみぽーち':'ぬいポーチ','すまーとふぉんしょるだー':'スマホショルダー','せきゅあでじたる':'SDカード','くいっくれすぽんす':'クイックレスポンス','えれくとろにっくすぽーつ':'eスポーツ'}
groups.update({'ぶるーれいでぃすく':'ブルーレイ','ちょこれーとちっぷ':'チョコチップ','ちょこれーとばなな':'チョコバナナ','ちょこれーとそーす':'チョコソース','でこれーしょんしーる':'デコシール','たぶれっとこんぴゅーたー':'タブレット','かっぷあいすくりーむ':'カップアイス','あいすくりーむ':'アイスクリーム','まいくろほん':'マイクロホン'})
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
ids={x['id'] for x in p['items']}
for x in d['items']:
 if x['id'] in ids:continue
 group=groups[x['reading']];base=next((b for b in p['items'] if b['group']==group),None)
 if base:
  x.update(group=group,filename=base['filename'],assignment='shared-new',sourceId=base['sourceId'],credit=base['credit'],reuseReason='略語と元の言葉で同じ対象を示すため画像を共有。')
  for a in p['newImages']+p['diagrams']:
   if a['id']==base['sourceId']:a['sharedIds'].append(x['id'])
 elif x['reading'] in ('あいすくりーむ','まいくろほん'):
  rd='あいす' if x['reading']=='あいすくりーむ' else 'まいく';source=next(dict(id=i,**r) for i,r in enumerate(live,1) if r['reading']==rd)
  x.update(group=group,filename=source['image_asset'].split('/')[-1],assignment='reused',sourceId=source['id'],credit=source['image_credit'],reuseReason='既存の略称と同じ対象。画像の被写体と今回の語義を確認して共有。')
  p['reuseReviews'].append(dict(group=group,targets=[x['id']],candidates=[source]))
 else:
  x.update(group=group,filename=f'expansion512c-word-{x["id"]}.png',assignment='diagram',sourceId=x['id'],credit='プログラム生成図',reuseReason='名称の由来となった「素早い応答」を図示。QRコード自体の画像は共有しない。')
  p['diagrams'].append(dict(x,sharedIds=[x['id']]))
 p['items'].append(x)
(OUT/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(words=len(p['items']),diagrams=len(p['diagrams']),illustrations=len(p['newImages']))))
