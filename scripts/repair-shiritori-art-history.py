"""Correct this intake with an append-only history entry and prepare missed works."""
import json,csv,re,hashlib,collections,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'data/dictionary-imports/art-history-sources';BASE=ROOT/'data/dictionary-imports/2026-10-28-art-history';SUP=ROOT/'data/dictionary-imports/2026-10-28-art-history-supplement'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
sha=lambda b:hashlib.sha256(b).hexdigest()
fields='reading word meaning imagequery level imagequery_en image_asset image_mode image_credit'.split()
def hira(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
old=read(BASE.with_suffix('.review.json'));cs=read(SRC/'candidates.json');ed=read(SRC/'editorial-decisions.json');ex=read(SRC/'extracts.json');raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf8').splitlines()));history=read(ROOT/'data/dictionary-imports/history.json');assert history[-1]['afterSha256']==sha(raw)
manual={'イサーク・マッサとベアトリクス・ファン・デル・ラーンの結婚肖像画':'いさーくまっさとべあとりくすふぁんでるらーんのけっこんしょうぞうが','アッリーゴ、ピエトロ、アモンの三人の肖像画':'あっりーごぴえとろあもんのさんにんのしょうぞうが','ドルドレヒトのマース川':'どるどれひとのまーすがわ','エマニュエル＝ジョゼフ・シエイエスの肖像':'えまにゅえるじょぜふしえいえすのしょうぞう','聖ヒエロニムスの聖母':'せいひえろにむすのせいぼ','洗礼者聖ヨハネといる聖家族 (パルミジャニーノ)':'せんれいしゃせいよはねといるせいかぞく','第九の波':'だいきゅうのなみ','狩猟の獲物、野菜と果物のある静物':'しゅりょうのえものやさいとくだもののあるせいぶつ'}
def fix(x):
 x=dict(x)
 if '、' in x['word']:
  lead=ex[str(x['pageid'])]['extract'];title=x['word'];m=re.search(r'^[『「]?'+re.escape(title)+r'[』」]?[ 　]*[（(]([ぁ-ゖァ-ヶー・ 　、]+)',lead)
  if m:x['reading']=re.sub('[・ 　、]','',hira(m.group(1)))
 if x['articleTitle'] in manual:x['reading']=manual[x['articleTitle']]
 x['reading']=x['reading'].replace('ひじり','せい').replace('せいぼこ','せいぼし')
 if x['word'].startswith('ナスタージョ'):
  parts={'第一話':'だいいちわ','第二話':'だいにわ','第三話':'だいさんわ'}
  for k,v in parts.items():
   if k in x['word']:x['reading']='なすたーじょでりおねすてぃのものがたり'+v
 if not re.fullmatch('[ぁ-ゖー]+',x['reading']):raise ValueError(x)
 return x
final=[];changes=[]
for x in old:
 y=fix(x);r=rows[x['id']-1];assert all(r[k]==x[k] for k in fields)
 if x['reading']!=y['reading']:
  y['readingSource']='記事の題名全体と読みを再照合・編集補正';after={k:y[k] for k in fields};changes.append(dict(action='edit',beforeId=x['id'],before=dict(r),after=after));rows[x['id']-1]=after
 final.append(y)
if changes:
 lines=raw.decode('utf8').splitlines()
 for c in changes:lines[c['beforeId']]=','.join(c['after'][k] for k in fields)
 after=('\n'.join(lines)+'\n').encode('utf8')
 assert after.split(b'\n')[:read(BASE.with_suffix('.summary.json'))['baselineRows']+1]==raw.split(b'\n')[:read(BASE.with_suffix('.summary.json'))['baselineRows']+1]
 save(BASE.with_suffix('.corrections.json'),changes)
 history.append(dict(type='reviewed-corrections',batch='data/dictionary-imports/2026-10-28-art-history.corrections.json',sourceRows=len(rows),currentRows=len(rows),currentBeforeIds=list(range(1,len(rows)+1)),beforeSha256=sha(raw),afterSha256=sha(after),changes=changes));save(ROOT/'data/dictionary-imports/history.json',history);(ROOT/'whitelist.csv').write_bytes(after)
 coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json');grades=read(ROOT/'data/shiritori-grade-decisions.json')
 for c in changes:
  i=c['beforeId']-1;r=c['after'];coverage[i].update(reading=r['reading'],word=r['word'],meaning=r['meaning']);updates['entries'][i]['text']=[r['reading'],r['word'],r['meaning']]
 grades['sourceSha256']=sha(after);save(ROOT/'data/shiritori-grade-decisions.json',grades);save(ROOT/'data/image-coverage/review-2026-10-10.json',coverage)
 updates['csvSha256']=sha(after);updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode());(ROOT/'data/image-coverage/review-updates.json').write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
 subprocess.run([sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py'],cwd=ROOT,check=True)
prev={x['articleTitle'] for x in old};supp=[]
for x in cs:
 if x['articleTitle'] in prev or x['articleTitle'] in ed['exclude']:continue
 c=dict(x);c.update(ed['corrections'].get(c['articleTitle'],{}));c=fix(c)
 if c['readingSource']=='機械読み候補（要確認）' and re.search('[一-龥々]',c['word']):
  assert c['articleTitle'] in ed['confirmedReadings'];c['readingSource']='機械読み候補を編集確認'
 y=dict(old[0]);y.update(c);y.pop('priority',None);y.update(id=len(rows)+len(supp)+1,lexicalSource=c['sourceUrl'],attribution='日本語版Wikipedia「'+c['articleTitle']+'」の執筆者',sourceHistory='https://ja.wikipedia.org/w/index.php?title='+__import__('urllib.parse',fromlist=['quote']).quote(c['articleTitle'])+'&action=history')
 supp.append(y)
assert any(x['word']=='星月夜' for x in supp)
SUP.with_suffix('.csv').write_text(','.join(fields)+'\n'+'\n'.join(','.join(x[k] for k in fields) for x in supp)+'\n',encoding='utf8',newline='\n');save(SUP.with_suffix('.review.json'),supp)
raw=(ROOT/'whitelist.csv').read_bytes();save(SUP.with_suffix('.summary.json'),dict(registered=False,beforeSha256=sha(raw),baselineRows=len(rows),added=len(supp),categories=dict(collections.Counter(x['category'] for x in supp))))
save(BASE.with_suffix('.final-review.json'),final+supp)
print(json.dumps(dict(corrected=len(changes),supplement=len(supp),totalAdded=len(final)+len(supp)),ensure_ascii=False))
