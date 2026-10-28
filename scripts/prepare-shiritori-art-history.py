import json,csv,re,sys,unicodedata,collections,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'data/dictionary-imports/art-history-sources'
sys.path.insert(0,str(SRC/'python-deps'))
from pykakasi import kakasi
K=kakasi()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
def hira(s):
 s=unicodedata.normalize('NFKC',s)
 return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
def norm(s):return re.sub(r'[\s・･「」『』〈〉《》、。・:：―‐−—-]','',unicodedata.normalize('NFKC',s)).lower()
def bare(s):return re.sub(r'\s*[（(].*?[）)]','',s).strip()
def unparen(s):
 old=None
 while old!=s:old=s;s=re.sub(r'[（(][^()（）]*[）)]','',s)
 s=re.sub(r'[（(][^。]*?(?=は[、 ])','',s)
 return s.replace('）','').replace(')','')
oldlines=(ROOT/'whitelist.csv').read_text(encoding='utf8').splitlines()
batchsummary=ROOT/'data/dictionary-imports/2026-10-28-art-history.summary.json'
if batchsummary.exists():oldlines=oldlines[:read(batchsummary)['baselineRows']+1]
old=list(csv.DictReader(oldlines))
existing=collections.defaultdict(list)
for x in old:existing[norm(x['word'])].append(x)
ess={}
for line in (SRC/'essentials.tsv').read_text(encoding='utf8').splitlines():
 w,r,m=line.split('\t');ess[norm(w)]=(w,r,m)
pages=read(SRC/'pages.json');extracts=read(SRC/'extracts.json');items=[];excluded=[]
for p in pages:
 e=extracts.get(str(p['pageid']),{});title=p['title'];w=bare(title);lead=e.get('extract','').strip().split('\n')[0];key=norm(w)
 def reject(reason):excluded.append(dict(title=title,reason=reason))
 if not lead:reject('導入文なし');continue
 if any(t in title for t in ['一覧','事件','殺人','強姦','児童','ポルノ','外陰','膣','陰茎','美術館','博物館','大学','協会','株式会社','工業','協同組合','プロジェクト','映画','集団','委員会']):reject('対象外の項目');continue
 if re.search(r'\d{4}年.{0,20}(生まれ|出身|生\s*[-－–〜～]|生、)|\d{4}年.{0,25}[-－–〜～].{0,25}\d{4}年',lead[:250]) and not re.search(r'絵画|作品|代表作|壁画|彫刻|版画|屏風|絵巻',lead[:180]):reject('人物項目');continue
 if re.search(r'(画家|彫刻家|美術家|陶芸家|建築家|美術史家|教授|芸術家|写真家|書家|政治家|版画家)(である|であった)?。$',unparen(lead).split('。')[0]+'。'):reject('人物項目');continue
 if re.search(r'会社|団体|美術館|博物館|出版社|研究者|芸術家集団|美術団体',unparen(lead)[:170]) and not re.search(r'絵画|代表作|油彩|油絵|板絵|様式|技法|工芸品|屏風|絵巻',unparen(lead)[:120]):reject('団体・施設等');continue
 # Definitions come from the opening sentence of a fixed CC BY-SA article revision.
 clean=unparen(re.sub(r'\[\d+\]','',lead));clean=re.sub(r'\s+',' ',clean).replace(',','、')
 first=clean.split('。')[0]+'。'
 prefix=re.match(r'^[『「]?'+re.escape(w)+r'[』」]?(?:とは|は|と[はいう]+)[、 ]*',first)
 m=first[prefix.end():] if prefix else first
 override=key in ess
 if override and p['group']=='絵画作品':
  mm=ess[key][2];author=re.match(r'^(.+?)(?:の絵画|の版画|の屏風絵|の日本画|の水墨画|の彫刻|の肉筆画|の大作|の作で)',mm)
  if author and author.group(1) not in lead:override=False
 if p['category']=='Wikidata絵画・重点語' and not override and not re.search(r'絵画|油彩|版画|屏風|絵巻|壁画|[画絵図像]である|[画絵図像]。|彫刻|芸術|技法|美術|画材|絵具|絵の具|[派]。',lead[:350]):reject('同名の別分野ページ');continue
 if override:
  w,r,m=ess[key];readingSource='編集確認（重点語）';priority=0
 else:
  r='';readingSource='';priority=1
  opening=lead[:min(200,len(lead))]
  # Use the supplied Japanese pronunciation only when it directly follows the title.
  mt=re.search(r'^[『「]?'+re.escape(w)+r'[』」]?[ 　]*[（(]([ぁ-ゖァ-ヶー・ 　]+)(?:[、,，）)])',opening)
  if mt:
   candidate=re.sub(r'[・ 　]','',hira(mt.group(1)))
   if re.fullmatch('[ぁ-ゖー]+',candidate):r=candidate;readingSource='記事冒頭の読み'
  if not r:
   chunks=re.split(r'[=＝・ 　「」『』、。:：―‐−—-]+',w)
   r=''.join(''.join(t['hira'] for t in K.convert(c)) if re.search('[一-龥々]',c) else hira(c) for c in chunks);r=hira(r);readingSource='機械読み候補（要確認）'
 if not re.fullmatch('[ぁ-ゖー]+',r) or len(r)>45:reject('読み未確定・長すぎる');continue
 if not 6<=len(m)<=600 or '。' not in clean or any(t in m for t in ['曖昧さ回避','を参照','加筆','要出典']):reject('定義を要編集');continue
 if key in existing:
  # Do not count stylistic variants and refreshed definitions as new vocabulary.
  if not re.search(r'絵画|壁画|版画|屏風|絵巻|の彫刻|の作品',m) or any(re.search(r'絵画|壁画|版画|屏風|絵巻|の彫刻|の作品',x['meaning']) for x in existing[key]):reject('既存語と同義・表記違い');continue
 rev=e.get('revisions',[{}])[0].get('revid');url='https://ja.wikipedia.org/w/index.php?oldid='+str(rev)
 items.append(dict(word=w,reading=r,meaning=m,category=p['group'],articleTitle=title,pageid=p['pageid'],revision=rev,sourceUrl=url,readingSource=readingSource,priority=priority,sourceCategory=p['category']))
# One entry per underlying article and no alternate spelling padding.
items.sort(key=lambda x:(x['priority'],{'流派・美術史':0,'技法・画材':1,'工芸・装飾':2,'彫刻作品':3,'絵画作品':4}[x['category']],x['pageid']))
seen=set();unique=[]
for x in items:
 k=(norm(x['word']),norm(x['meaning']))
 if k in seen:continue
 seen.add(k);unique.append(x)
(SRC/'candidates.json').write_text(json.dumps(unique,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(SRC/'excluded.json').write_text(json.dumps(excluded,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(dict(candidates=len(unique),categories=dict(collections.Counter(x['category'] for x in unique)),readingSources=dict(collections.Counter(x['readingSource'] for x in unique)),exclusions=dict(collections.Counter(x['reason'] for x in excluded))),ensure_ascii=False))
