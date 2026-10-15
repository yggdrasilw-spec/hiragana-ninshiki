"""Record the pre-publication correction of a confused regional food name."""
import csv,hashlib,io,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-15-expansion512d'
OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
word='イタリアンスパゲッティ'
meaning='ケチャップなどで味つけしたスパゲッティの呼び名。名古屋などでは、卵をしいた鉄板で出すものもある。'
url='https://www.ambre.co.jp/kitchen.html'
before=(ROOT/'whitelist.csv').read_text(encoding='utf-8');lines=before.splitlines();header=lines[0].split(',')
id=next(i for i,l in enumerate(lines) if i and l.split(',')[1]==word)
old=lines[id];cols=old.split(',');old_meaning=cols[2]
if old_meaning==meaning:print('Correction already recorded');raise SystemExit
cols[2]=meaning;lines[id]=','.join(cols);after='\n'.join(lines)+'\n'
history=read(DATA/'history.json');assert history[-1]['afterSha256']==sha(before)
reason='新潟の「イタリアン」（焼きそばにソースをかける料理）との混同を除去。名古屋の提供店の説明と照合。生成画像はケチャップ系スパゲッティの提供例として確認。'
change=dict(originalId=id,before=old,after=lines[id],reason=reason,sources=[url,'https://www.kagome.co.jp/products/recipe/Z6507/'])
history.append(dict(type='vocabulary-corrections',batch=f'data/corrections/{NAME}.json',beforeSha256=sha(before),afterSha256=sha(after),sourceRows=len(lines)-1,currentOriginalIds=list(range(1,len(lines))),changes=[change]))
(ROOT/'whitelist.csv').write_bytes(after.encode('utf-8'));save(DATA/'history.json',history)
save(ROOT/'data/corrections'/f'{NAME}.json',dict(date='2026-10-16',changes=[change]))
for path,key in [(OUT/'plan.json','items'),(DATA/(NAME+'.review.json'),None),(ROOT/'data/image-coverage/review-2026-10-10.json',None)]:
 data=read(path);items=data[key] if key else data
 for x in items:
  if x.get('id')==id:
   x['meaning']=meaning
   if 'meaningReason' in x:x['meaningReason']=reason+' '+meaning
   if 'sources' in x:x['sources']=list(dict.fromkeys(x['sources']+[url]))
   if 'scene' in x:x['scene']=word+'：'+meaning
 save(path,data)
source=read(DATA/(NAME+'.source.json'))
for x in source['rows']:
 if x['word']==word:x['sources']=list(dict.fromkeys(x['sources']+[url]));x['lexicalSource']='名古屋の提供店・メーカー料理説明の参照';x['senseCorrection']=reason
 # Do not cite the Japanese B.League as the source for American NBA names.
 if any(k in x['word'] for k in ['レイカーズ','ウォリアーズ','セルティックス','ブルズ','ニックス']):x['sources']=[u for u in x['sources'] if u!='https://www.bleague.jp/club/']+['https://www.nba.com/teams']
save(DATA/(NAME+'.source.json'),source)
manifest=read(ROOT/'assets/shiritori/manifest.json')
for a in manifest['assets']:
 if a.get('word')==word and a['file'].startswith('expansion512d-'):
  a['meaning']=meaning;a['review']='編集確認済み：ケチャップ系のスパゲッティの提供例。'+reason
  for alias in a['aliases']:alias['meaning']=meaning;alias['sourceReview']=a['review']
save(ROOT/'assets/shiritori/manifest.json',manifest)
for path in [DATA/(NAME+'.csv'),ROOT/'data/batches'/f'{NAME}-images.csv']:
 text=path.read_text(encoding='utf-8');reader=csv.DictReader(io.StringIO(text));rows=list(reader);fields=reader.fieldnames
 for r in rows:
  if r['word']==word:r['meaning']=meaning
 with path.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
editorial=DATA/(NAME+'.editorial.txt');editorial.write_text(editorial.read_text(encoding='utf-8').replace(old_meaning,meaning),encoding='utf-8')
for path in [OUT/'summary.json',DATA/(NAME+'.summary.json')]:
 s=read(path);s['afterSha256']=sha(after);save(path,s)
print(json.dumps(dict(correctedId=id,word=word,meaning=meaning),ensure_ascii=False))
