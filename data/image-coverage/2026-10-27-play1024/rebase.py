import json,csv,hashlib,re
from pathlib import Path
H=Path(__file__).resolve().parent;B=H/'2026-10-27-play1024';R=Path('C:/Users/user/hiragana-ninshiki')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
s=read(B.with_suffix('.summary.json'));raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8').splitlines()));rows=read(B.with_suffix('.review.json'))
prefix=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n'
if hashlib.sha256(prefix).hexdigest()!=s['beforeSha256']:
 first=read(H/'rebase.json');n=first['beforeBaselineRows'];trusted=first['beforeSha256']
 original=b'\n'.join(raw.split(b'\n')[:n+1])+b'\n'
 history=read(R/'data/dictionary-imports/history.json')
 assert hashlib.sha256(original).hexdigest()==trusted,'Pre-existing dictionary was changed'
 assert history[-1]['beforeSha256']==trusted and history[-1]['afterSha256']==hashlib.sha256(raw).hexdigest(),'Concurrent changes lack matching import evidence'
keys={(x['reading'],x['word'],x['meaning']) for x in old};overlap=[x['word'] for x in rows if (x['reading'],x['word'],x['meaning']) in keys];assert not overlap,overlap
offset=len(old)-s['baselineRows'];assert offset>=0
ids={x['id']:x['id']+offset for x in rows}
for x in rows:
 x.setdefault('plannedIdBeforeRebase',x['id']);x['id']=ids[x['id']]
 if any(y['reading']==x['reading'] for y in old):x['distinctSenseReason']='既存語と読みが同じでも別の作品・商品・カード・遊びを指す意味。既存の意味は保持。正式名の略称には同じ画像と説明を割り当てる。'
for name in ['manifest-additions.json','manifest-reused.json']:
 a=read(H/name)
 for entry in a:
  for x in entry['aliases']:
   if x['id'] in ids:x['id']=ids[x['id']]
 save(H/name,a)
record=dict(beforeBaselineRows=s['baselineRows'],afterBaselineRows=len(old),beforeSha256=s['beforeSha256'],afterSha256=hashlib.sha256(raw).hexdigest(),idOffset=offset,overlap=overlap,assetPolicy='画像にはIDを印刷していないため既存ファイル名・ハッシュを維持。manifestと審査記録の語IDだけ最新の行へ対応付ける。')
if (H/'rebase.json').exists():
 oldrecord=read(H/'rebase.json');save(H/'rebase-initial.json',oldrecord)
save(H/'rebase.json',record)
s.update(baselineRows=len(old),beforeSha256=hashlib.sha256(raw).hexdigest(),newReadings=len({x['reading'] for x in rows}-{x['reading'] for x in old}));save(B.with_suffix('.summary.json'),s);save(B.with_suffix('.review.json'),rows)
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
B.with_suffix('.csv').write_text(header+'\n'+'\n'.join(','.join(str(x[k]) for k in header.split(',')) for x in rows)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(newBaseline=len(old),offset=offset,newReadings=s['newReadings'])))
