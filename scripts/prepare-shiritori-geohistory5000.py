"""Prepare a source-bound historical-person / natural-geography intake; no live writes."""
import csv,json,hashlib,re,unicodedata,collections,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--baseline',type=Path,default=ROOT/'whitelist.csv');args=parser.parse_args()
OUT=args.output;OUT.mkdir(parents=True,exist_ok=True);SRC=ROOT/'data/geohistory5000/sources'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def norm(s):return re.sub(r'[\s・＝=\-‐‑–—()（）]','',unicodedata.normalize('NFKC',s))
def kana(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(s))
before=args.baseline.read_bytes();old=list(csv.DictReader(before.decode('utf-8-sig').splitlines()))
oldwords={norm(x['word']) for x in old};oldread={x['reading'] for x in old}
historyNames=[(norm(x['word']),x['reading']) for x in old if re.search('武将|大名|公卿|天皇|藩主|藩士|将軍|革命家|哲学者|政治家|歴史家|思想家|探検家|浮世絵師|歌人|儒学者|国学者',x['meaning']) and len(norm(x['word']))>=2]
rejected=[];items=[];seenwords=set();seenreads=set();seenids=set();files=[]
suffixes={'湖':'こ','山脈':'さんみゃく','海':'かい','湾':'わん','半島':'はんとう','高原':'こうげん','盆地':'ぼんち','砂漠':'さばく','諸島':'しょとう','海峡':'かいきょう','平原':'へいげん','平野':'へいや','島':'とう'}
inputs=[('japan-persons','日本史')]+[(p.stem,'世界史' if p.name.startswith('world-') else '地理') for p in sorted(SRC.glob('*.json')) if p.stem.startswith(('world-','geo-'))]
for filename,subject in inputs:
 p=SRC/(filename+'.json')
 if not p.exists():continue
 data=json.loads(p.read_text(encoding='utf-8'))
 if not data['results']['bindings']:continue
 files.append(dict(file=p.name,sha256=sha(p.read_bytes()),partialResponse=data.get('partialResponse',False),bindings=len(data['results']['bindings'])))
 groups=collections.defaultdict(list)
 for b in data['results']['bindings']:groups[b['item']['value'].split('/')[-1]].append({k:v['value'] for k,v in b.items()})
 for qid,rows in sorted(groups.items(),key=lambda kv:int(kv[0][1:])):
  b=rows[0];word=re.sub(r'\s+[（(].*','',b['label']);description=b['description'];reason=None
  if any(t in description for t in ['架空','伝説','神話','声優','プロレス','競馬','子役']):reason='対象外・非実在等'
  if len(description)<7 or len(description)>200:reason='説明の具体性または長さ'
  if re.search(r'[?？]|要出典|未詳|不明|のこと。$|の当て字',description):reason='不確かな説明・参照だけの説明'
  if any(t in description for t in ['派人','著作化']) or len(description.split('。')[0])>140:reason='出典の誤記候補・一文が長過ぎる説明'
  if word=='細川藤孝':reason='出典の仮名が別名の幽斎に対応しているため保留'
  aliases={'上杉治憲':['上杉鷹山'],'徳川光圀':['水戸黄門'],'大石良雄':['大石内蔵助'],'最上徳内':['最上常矩'],'山内一豊':['山内伊右衛門'],'加藤清正':['虎之助'],'平直方':['北条直方'],'徳川信康':['松平信康'],'後西院天皇':['後西天皇']}
  if any(norm(a) in oldwords for a in aliases.get(word,[])):reason='確認できた既存人物の別名'
  deathYears=[int(x['death'][:4]) for x in rows if re.match(r'\d{4}-',x.get('death',''))]
  if deathYears and subject=='日本史':
   if '江戸時代後期' in description and max(deathYears)<1750:reason='出典の時代と没年に不整合'
   if description.startswith('明治時代') and max(deathYears)<1868:reason='出典の時代と没年に不整合'
   if '戦国時代' in description and max(deathYears)<1450:reason='出典の時代と没年に不整合'
  if subject=='日本史' and not re.search('日本|江戸|明治|戦国|平安|鎌倉|室町|安土|幕末|奈良|飛鳥|大和|公家|公卿|大名|藩士|幕臣|藩主|天皇|皇族|家臣|藩|武将',description):reason='日本史の文脈が不明'
  if subject!='地理' and re.search('およびその|総称|称号|名乗った通称',description):reason='単一人物の説明ではない候補'
  if subject=='世界史' and not re.search('王|皇帝|君主|政治|軍人|将軍|革命|哲学|思想|教皇|神学|探検|航海|歴史|経済|社会学|地理学|宰相|大統領|首相|総督|独立|女帝|外交|民族|統治|司教|枢機卿|大臣',description):reason='歴史分野の役割が不明'
  if subject=='世界史' and not all(x.get('death','')<'1950' for x in rows):reason='1950年以降に没した人物・今回の時代対象外'
  readings={kana(x['reading']) for x in rows if x.get('reading')}
  readingCorrection=None
  if subject=='日本史':
   if len(readings)!=1:reason='仮名表記が複数・要個別確認';reading=next(iter(readings),'')
   else:reading=next(iter(readings))
   for clan,prefix in [('源','みなもと'),('藤原','ふじわら'),('平','たいら')]:
    if word.startswith(clan) and reading.startswith(prefix) and not reading.startswith(prefix+'の'):
     reason='氏名の助詞「の」が出典の仮名にない・要個別確認'
  else:
   reading=kana(word)
   if subject=='地理':
    for end,sound in sorted(suffixes.items(),key=lambda x:-len(x[0])):
     if word.endswith(end):reading=kana(word[:-len(end)])+sound;break
  # Island names have irregular tou/shima/jima readings: do not infer them.
  if subject=='地理' and word.endswith('島') and not word.endswith('諸島'):reason='島の接尾辞の読みを未確認'
  if not re.fullmatch('[ぁ-ゖー]+',reading) or not 2<=len(reading)<=35 or reading.startswith('ん'):reason='仮名形式・長さ'
  if re.search(r'[\r\n,]',word+description):reason='アプリのCSV形式に不適合'
  if any(x['label']!=b['label'] or x['description']!=description for x in rows):reason='出典内で名称または説明が不一致'
  if norm(word) in oldwords:reason='既存表記・別説明で水増ししない'
  if reading in oldread:reason='既存の同音語または別表記候補・要個別確認'
  if subject!='地理' and any(norm(word).endswith(w) and reading.endswith(r) for w,r in historyNames):reason='既存の歴史人物の姓・短縮名と一致する候補・要個別確認'
  if qid in seenids or norm(word) in seenwords or reading in seenreads:reason='同一対象・表記・読みの重複候補'
  if reason:rejected.append(dict(qid=qid,subject=subject,word=word,reason=reason));continue
  # Retain the complete CC0 source description; only normalize sentence punctuation.
  meaning=description.split('。')[0].lstrip('、。 ').rstrip('。')+'。'
  deaths={x.get('death','')[:4] for x in rows if re.match(r'\d{4}-',x.get('death',''))}
  if subject!='地理' and len(deaths)==1:
   year=next(iter(deaths))
   if year not in meaning:meaning+=str(int(year))+'年没。'
  source=dict(dataset='Wikidata',id=qid,url='https://www.wikidata.org/wiki/'+qid,title='Wikidata：'+word,license='CC0',licenseUrl='https://creativecommons.org/publicdomain/zero/1.0/',retrievedOn='2026-10-29',snapshot=filename+'.json',readingMethod='P1814の単一仮名表記' if subject=='日本史' else 'カタカナ名称をひらがなに変換'+('。地理接尾辞は固定の読み。島の読みの推測は除外。' if subject=='地理' else ''))
  x=dict(reading=reading,word=word,meaning=meaning,subject=subject,category=subject,genre='place' if subject=='地理' else 'society',source=source,sourceRecord=b)
  if readingCorrection:x['readingCorrection']=readingCorrection
  items.append(x);seenwords.add(norm(word));seenreads.add(reading);seenids.add(qid)
# Target is a floor. Keep the eligible source-backed set, rather than adding aliases to reach a quota.
for i,x in enumerate(items,len(old)+1):
 x.update(id=i,level=3,grade=5,imagequery=x['word'],imagequery_en='',image_asset='',image_mode='none',image_credit='',lexicalSource=x['source'],meaningReason='CC0の対象識別説明の最初の一文を使い句点と没年を整形。原文をsourceRecordに保存。事実の独立した全件再校閲ではない。',ageReason='歴史人物・自然地理の詳しい固有名として意味別レベル5。',imageReason='説明のみ。外部画像検索を行わない。')
header=before.decode('utf-8-sig').splitlines()[0]
base=OUT/'2026-10-29-geohistory5000'
base.with_suffix('.csv').write_text(header+'\n'+''.join(','.join(str(x[k]) for k in header.split(','))+'\n' for x in items),encoding='utf-8',newline='\n')
save(base.with_suffix('.review.json'),items);save(base.with_suffix('.excluded.json'),rejected)
summary=dict(registered=False,baselineRows=len(old),beforeSha256=sha(before),added=len(items),subjects=dict(collections.Counter(x['subject'] for x in items)),newReadings=len(items),endingN=sum(x['reading'].endswith('ん') for x in items),explanationOnly=len(items),source='Wikidata CC0。出典に基づく選定・形式検証。全件の独立した専門家校閲は未実施。',target=5000,targetMet=len(items)>=5000)
save(base.with_suffix('.summary.json'),summary);save(base.with_suffix('.sources.json'),dict(retrievedOn='2026-10-29',files=files,license='CC0',licenseUrl='https://www.wikidata.org/wiki/Wikidata:Licensing',queries=[f['file'].replace('.json','.rq') for f in files],limits=['人名と自然地理の固有名を中心とした拡充。制度・事件・概念を含む教科書索引全体の網羅ではない。','出典の仮名・説明の誤りが残る可能性があり、独立した全件専門家校閲ではない。','同じ読みの候補は別表記による増量を避けるため保留した。']))
print(json.dumps(summary,ensure_ascii=False));print('EXCLUDED',len(rejected));print('SAMPLE',json.dumps([{k:x[k] for k in ['word','reading','meaning','subject']} for x in items[::max(1,len(items)//40)]],ensure_ascii=False))
