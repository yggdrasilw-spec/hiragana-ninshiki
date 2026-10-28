"""Prepare the reviewed 2,000-entry art intake; never mutates the live dictionary."""
import csv,json,hashlib,collections,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'data/dictionary-imports/art-history-sources';BASE=ROOT/'data/dictionary-imports/2026-10-28-art-history'
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
if BASE.with_suffix('.summary.json').exists() and read(BASE.with_suffix('.summary.json'))['registered']:raise SystemExit('Already imported; do not regenerate row IDs.')
candidates=read(SRC/'candidates.json');decisions=read(SRC/'editorial-decisions.json');raw=(ROOT/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf8').splitlines()))
items=[];excluded=[]
for c in candidates:
 if c['articleTitle'] in decisions['exclude']:excluded.append(dict(**c,excludeReason=decisions['exclude'][c['articleTitle']]));continue
 if c['articleTitle'] in decisions.get('corrections',{}):c.update(decisions['corrections'][c['articleTitle']])
 if c['readingSource']=='機械読み候補（要確認）' and re.search('[一-龥々]',c['word']):
  if c['articleTitle'] not in decisions.get('confirmedReadings',[]):excluded.append(dict(**c,excludeReason='漢字の機械読みを未確認'));continue
  c['readingSource']='機械読み候補を編集確認'
 r=dict(id=len(old)+len(items)+1,reading=c['reading'],word=c['word'],meaning=c['meaning'],imagequery='',level='3',imagequery_en='',image_asset='',image_mode='none',image_credit='',**{k:v for k,v in c.items() if k not in ['reading','word','meaning','priority']})
 r.update(lexicalSource=c['sourceUrl'],meaningReason='固定版の百科事典導入文をもとに語義を限定。重点語は独自の短い説明に編集。',ageReason='専門的な美術史・作品知識を要する語義のためレベル5。画像なしで説明を表示。',distinctSenseReason='出典記事の対象はこの美術用語または美術作品。既存の同音語とは定義・対象が異なる。',sourceLicense='CC BY-SA 4.0',attribution='日本語版Wikipedia「'+c['articleTitle']+'」の執筆者',sourceHistory='https://ja.wikipedia.org/w/index.php?title='+__import__('urllib.parse',fromlist=['quote']).quote(c['articleTitle'])+'&action=history')
 items.append(r)
assert len(items)>2000,('Not enough reviewed entries',len(items))
assert len({(x['reading'],x['word'],x['meaning']) for x in items})==len(items)
fields=['reading','word','meaning','imagequery','level','imagequery_en','image_asset','image_mode','image_credit']
for x in items:
 assert re.fullmatch('[ぁ-ゖー]+',x['reading'])
 assert all(not any(c in str(x[k]) for c in ',\r\n') for k in fields)
BASE.with_suffix('.csv').write_text(','.join(fields)+'\n'+'\n'.join(','.join(x[k] for k in fields) for x in items)+'\n',encoding='utf8',newline='\n')
save(BASE.with_suffix('.review.json'),items);save(BASE.with_suffix('.excluded.json'),excluded)
s=dict(registered=False,beforeSha256=hashlib.sha256(raw).hexdigest(),baselineRows=len(old),added=len(items),categories=dict(collections.Counter(x['category'] for x in items)),readingSources=dict(collections.Counter(x['readingSource'] for x in items)))
save(BASE.with_suffix('.summary.json'),s)
save(BASE.with_suffix('.sources.json'),dict(retrievedOn='2026-10-28',license='Wikipedia text adapted under CC BY-SA 4.0; Wikidata facts CC0',policy='名称と定義は個別の版番号付き記事に対応。読みは記事冒頭・重点語編集・機械候補の編集確認を区別。各作品を所蔵美術館で一件ずつ照合したものではない。',wikipedia='https://ja.wikipedia.org/',licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/',importantReferences={'星月夜':'https://www.moma.org/collection/works/79802'},sources=[{k:x[k] for k in ['id','articleTitle','pageid','revision','sourceUrl','sourceHistory','attribution','sourceLicense','readingSource']} for x in items]))
print(json.dumps(s,ensure_ascii=False))
