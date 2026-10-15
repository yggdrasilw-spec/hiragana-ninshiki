"""Prepare a separate named-entity/music intake without touching live data."""
import csv, hashlib, html, json, re, unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-15-expansion512e'
DATA=ROOT/'data/dictionary-imports'
OUT=ROOT/'data/image-coverage'/NAME
CACHE=Path('C:/Users/user/.cache/shiritori-qa/expansion512e-sources')
OUT.mkdir(parents=True,exist_ok=True)
KANA=str.maketrans({chr(i):chr(i-96) for i in range(0x30a1,0x30f7)})
def norm(s):return unicodedata.normalize('NFKC',s).casefold().translate(KANA).replace('・','').replace(' ','').replace('　','')
def reading(s):return re.sub('[^ぁ-ゖー]','',norm(s))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
reserved_readings=set();reserved_words=set();reservation_files=[]
def reserve(r):
 if isinstance(r,dict):
  if r.get('reading'):reserved_readings.add(r['reading'])
  if r.get('word'):reserved_words.add(norm(r['word']))
  for v in r.values():
   if isinstance(v,(dict,list)):reserve(v)
 elif isinstance(r,list):
  for x in r:reserve(x)
for folder in [DATA,ROOT/'data/image-coverage']:
 for p in folder.rglob('*'):
  if not p.is_file() or NAME in str(p):continue
  if p.suffix=='.json' and (folder==DATA or p.name in ['plan.json','draft.json','candidates.json']):
   try:reserve(json.loads(p.read_text(encoding='utf-8-sig')));reservation_files.append(str(p.relative_to(ROOT)))
   except (ValueError,UnicodeError):pass
  if folder==DATA and p.suffix=='.csv':
   try:
    for r in csv.DictReader(p.open(encoding='utf-8-sig')):reserve(r)
    reservation_files.append(str(p.relative_to(ROOT)))
   except (UnicodeError,csv.Error):pass
  if folder==DATA and p.suffix in ['.txt','.tsv']:
   for line in p.read_text(encoding='utf-8-sig').splitlines():
    for token in line.split('|'):
     m=re.match(r'^([ぁ-ゖー]+)(?:[ \t]|$)',token.strip())
     if m:reserved_readings.add(m[1])
   reservation_files.append(str(p.relative_to(ROOT)))
blocked={r['reading'] for r in live};words={norm(r['word']) for r in live}
rules=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)',line,re.I)
 rules.append((m[1].lower(),norm(m[2].strip())) if m else ('contains',norm(line)))
pool=[];excluded=[];seen=set();seenwords=set()
def add(word,rd,meaning,category,sources,evidence=None):
 rd=norm(rd);w=norm(word)
 reason=('existing-reading' if rd in blocked else 'reserved-reading' if rd in reserved_readings else 'existing-spelling' if w in words else 'reserved-spelling' if w in reserved_words else 'duplicate-reading' if rd in seen else 'duplicate-spelling' if w in seenwords else None)
 if not re.fullmatch('[ぁ-ゖー]+',rd):reason='invalid-reading'
 if any(rd==p if mode=='exact' else p in rd for mode,p in rules):reason='blacklist'
 # A short character name must not duplicate an already registered full name.
 franchise={'ドラゴンボール':'ドラゴンボール','HUNTER×HUNTER':'HUNTER','北斗の拳':'北斗の拳'}.get(category)
 if franchise and len(w)>=3:
  for r in live:
   if franchise.casefold() in r['meaning'].casefold() and (w in norm(r['word']) or norm(r['word']) in w):
    reason='existing-entity-alias';break
 if reason:excluded.append(dict(word=word,reading=rd,category=category,reason=reason));return
 assert not any(c in meaning for c in ',\r\n'),word
 seen.add(rd);seenwords.add(w)
 pool.append(dict(reading=rd,word=word,meaning=meaning,category=category,level=3,sources=sources,sourceEvidence=evidence))

urls={
 '楽器':['https://www.yamaha.com/ja/musical_instrument_guide/','https://www.gakkihaku.jp/'],
 '音楽ジャンル':['https://musicbrainz.org/genres'],
 '漫画':['https://www.shonenjump.com/j/sp_jumpbookstore/ichiran.html','https://www.shonenjump.com/j/'],
 'ドラゴンボール':['https://www.toei-anim.co.jp/tv/dragon/character/','https://www.toei-anim.co.jp/tv/dragon_s/chara/'],
 'モビルスーツ':['https://gundam-official.com/seed/seed/mecha/','https://gundam-official.com/seed/destiny/mecha/','https://g-witch.net/mobile-suit/','https://gundam-official.com/gquuuuuux/mecha/']}
source_texts={p.name:norm(html.unescape(p.read_text(encoding='utf-8'))) for p in CACHE.glob('*.html')}
for line in (DATA/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
 if not line or line.startswith('#'):continue
 if line.startswith('['):category=line[1:-1];continue
 name,meaning=line.split('|',1)
 word,rd=name.split('~') if '~' in name else (name,reading(name))
 if word=='ガンノード':word='ガンドノード';rd=reading(word)
 if category=='ドラゴンボール':meaning='『ドラゴンボール』の登場人物。'+meaning
 if category=='漫画':meaning='漫画作品の名前。'+meaning
 evidence=[]
 for filename,text in source_texts.items():
  if norm(word) in text:evidence.append(filename)
 add(word,rd,meaning,category,urls[category],evidence)

# Official Sanrio JSON includes the search reading; preserve the exact source
# field and profile URL, rather than guessing the pronunciation of a kanji name.
sanrio=json.loads((CACHE/'sanrio-names.json').read_text(encoding='utf-8'))
known={'こぎみゅん':'小麦粉の妖精で、ふわふわした白い姿。','ポチャッコ':'好奇心いっぱいのイヌの男の子。','クロミ':'黒いずきんとピンクのどくろが目印。','ハンギョドン':'中国生まれの半魚人で、人を笑わせることが好き。','マイスウィートピアノ':'マイメロディの友だちで、ピンクのヒツジの女の子。','あひるのペックル':'お人よしで歌が好きな、アヒルの男の子。','タキシードサム':'蝶ネクタイが似合う、ペンギンの男の子。','ディアダニエル':'キティの幼なじみで、カメラが好きな男の子。','チョコキャット':'黒い体と大きな目が目印の、ネコの男の子。','ウサハナ':'カラフルな体と長い耳が目印の、ウサギの女の子。','ハミングミント':'歌うことが好きな、コジカの女の子。','パンダップル':'頭のリンゴが目印の、パンダの男の子。','ぼんぼんりぼん':'大きなリボンが目印の、ピンクのウサギの女の子。','コロコロクリリン':'小さな体で好奇心いっぱいの、ハムスターの男の子。','ゴロピカドン':'ゴロ・ピカ・ドンの、かみなりの三兄弟。'}
priority='ハローキティ マイメロディ クロミ シナモロール ポムポムプリン ポチャッコ ハンギョドン こぎみゅん あひるのペックル タキシードサム マイスウィートピアノ ウィッシュミーメル けろけろけろっぴ ぐでたま バッドばつ丸 リトルツインスターズ おさるのもんきち コロコロクリリン ディアダニエル チャーミーキティ ジュエルペット ミュークルドリーミー はなまるおばけ まるもふびより ぼんぼんりぼん チョコキャット ハミングミント ウサハナ シュガーバニーズ マロンクリーム パンダップル ルロロマニック フラガリアメモリーズ まいまいまいごえん はぴだんぶい ぼさにまる かぶきにゃんたろう ゴロピカドン ザシキブタ タイニーチャム'.split()
entries=[x for group in sanrio.values() for x in group]
entries.sort(key=lambda x:priority.index(x['name']) if x['name'] in priority else len(priority))
for x in entries:
 word=unicodedata.normalize('NFC',x['name']);raw=x['search']['word'].split(',')[2]
 rd=reading(raw)
 if word=='まるもふびより':rd='まるもふびより' # Official search field has a typo.
 if word in ['汽車','木馬','笑う女','ぷりぷりうんぴ〜ず']:continue
 if '（' in word or '＆' in word or '&' in word:continue
 add(word,rd,'サンリオのキャラクターの名前。'+known.get(word,'サンリオの公式キャラクター一覧で紹介されている。'),'サンリオ',[x['url']],dict(file='sanrio-names.json',name=x['name'],searchReading=raw,profile=x['url']))

arc={'hunter-other1':'ハンター試験編','hunter-other2':'ゾルディック家編','hunter-other3':'天空闘技場編','hunter-other4':'幻影旅団編','hunter-other5':'グリードアイランド編','hunter-other6':'キメラアント編','hunter-ant':'キメラアント編'}
hdesc={'ネフェルピトー':'キメラアントの王を守る護衛の一人。','シャウアプフ':'キメラアントの王を守る護衛の一人。','モントゥトゥユピー':'キメラアントの王を守る護衛の一人。','イカルゴ':'タコに似た姿で、キルアに協力する仲間。','コルト':'キメラアントの女王に仕える人物。','メレオロン':'姿や気配を隠す力を持つキメラアント。','コムギ':'盤上競技の軍儀が得意な少女。','ゴレイヌ':'グリードアイランドでゴンたちに協力するハンター。','ゲンスルー':'グリードアイランドでゴンたちに立ちはだかる人物。','アベンガネ':'人にかけられた念を取りのぞく力を持つハンター。','レイザー':'グリードアイランドの運営に関わる人物。','カナリア':'ゾルディック家で働き、門を守る少女。','ゴトー':'ゾルディック家に仕える執事。','ミルキ':'キルアの兄。','カルト':'キルアの弟。','ゼノ':'キルアの祖父。','シルバ':'キルアの父。','キキョウ':'キルアの母。','サトツ':'ハンター試験で試験官を務める人物。','ハンゾー':'ハンター試験でゴンと出会う、忍者の修行をした人物。','トンパ':'何度もハンター試験を受けている人物。','ポックル':'弓を得意とするハンター。','ズシ':'天空闘技場で修行する少年。','ウイング':'ズシの師匠で、ゴンたちにも念を教える人物。','センリツ':'音を聞き分ける力にすぐれたハンター。','ゼパイル':'古い品物の鑑定などでゴンたちに協力する人物。','モラウ':'大きなキセルを使う、経験豊かなハンター。','ノヴ':'出入りできる空間を作る力を持つハンター。'}
for word,slug,desc in [('ゴン','gon','父と同じハンターをめざす主人公。'),('キルア','kirua','ゴンと旅をする、ゾルディック家の少年。'),('クラピカ','kurapika','クルタ族の生き残りで、ゴンの仲間。'),('レオリオ','reorio','医者をめざしてハンター試験を受ける青年。'),('ヒソカ','hisoka','強い相手との勝負を求める人物。'),('カイト','kaito','ゴンにハンターの仕事を教えた人物。'),('クロロ','genei','幻影旅団を率いる人物。'),('マチ','genei','糸のようにした念を使う、幻影旅団の一員。'),('シズク','genei','特別な掃除機を使う、幻影旅団の一員。'),('シャルナーク','genei','情報や機械にくわしい、幻影旅団の一員。'),('ノブナガ','genei','刀を使う、幻影旅団の一員。'),('パクノダ','genei','記憶に関わる力を持つ、幻影旅団の一員。'),('フランクリン','genei','指先から念を放つ、幻影旅団の一員。'),('フィンクス','genei','腕を回して力を高める、幻影旅団の一員。'),('ウボォーギン','genei','大きな体と強い力を持つ、幻影旅団の一員。'),('フェイタン','genei','小柄ですばやく動く、幻影旅団の一員。'),('ボノレノフ','genei','体から出る音を使う、幻影旅団の一員。')]:
 add(word,reading(word),'『HUNTER×HUNTER』の登場人物。'+desc,'HUNTER×HUNTER',['https://www.ntv.co.jp/hunterhunter/character/'+slug+'.html'],dict(file='hunter.html' if slug!='genei' else 'hunter-spider.html',profile=slug))
for filename,part in arc.items():
 t=(CACHE/(filename+'.html')).read_text(encoding='utf-8')
 for word in dict.fromkeys(html.unescape(w) for w in re.findall(r'alt=["\']([^"\']+)',t)):
  if not re.fullmatch('[ァ-ヶー＝]+',word):continue
  if word in ['キャラクター','キメラアント','ギタラクル','バスガイド','ヤマイヌ','ヤマアラシ','スピン','リン']:continue
  page='kimera' if filename=='hunter-ant' else 'other_0'+filename[-1]
  add(word,reading(word),'『HUNTER×HUNTER』の登場人物。'+hdesc.get(word,part+'に登場する。'),'HUNTER×HUNTER',['https://www.ntv.co.jp/hunterhunter/character/'+page+'.html'],dict(file=filename+'.html',alt=word,arc=part))

hokuto=(CACHE/'hokuto-characters.html').read_text(encoding='utf-8')
names='ジュウザ レイ ラオウ カイオウ シュケン ユリア トキ リュウケン カーネル ジャギ 黒夜叉 シャチ ユダ ヒューイ ジャコウ リン ジャッカル デビルリバース リハク ケンシロウ サウザー アイン シュウ バット 赤鯱 アサム ウイグル ジュウケイ フドウ ヒョウ シュメ アミバ 牙族長 バラン ボルゲ オウカ ハート リュウガ ハン アイリ シュレン ジード ファルコ シン マミヤ'.split()
hd={'ケンシロウ':'北斗神拳を受け継ぐ主人公。','ラオウ':'拳王と呼ばれる、北斗の兄弟の長兄。','トキ':'医療にも拳法を生かす、北斗の兄弟の一人。','レイ':'南斗水鳥拳を使う、ケンシロウの仲間。','ジュウザ':'雲のように自由な生き方をする、南斗五車星の一人。','サウザー':'南斗鳳凰拳を使い、聖帝と名乗る人物。','ユリア':'ケンシロウと深く結びつく人物。','リン':'ケンシロウに助けられ、旅をともにする少女。','バット':'ケンシロウと旅をする、機械にもくわしい少年。','フドウ':'子どもたちを守る、南斗五車星の一人。','リハク':'海のリハクと呼ばれる、南斗五車星の一人。','ヒューイ':'風のヒューイと呼ばれる、南斗五車星の一人。','シュレン':'炎のシュレンと呼ばれる、南斗五車星の一人。','マミヤ':'村の人々を守り、ケンシロウたちと協力する人物。','アイリ':'レイの妹。','リュウケン':'北斗神拳をケンシロウたちに教えた師匠。','ジュウケイ':'北斗琉拳を教える師匠。','アイン':'娘を大切に思う賞金稼ぎ。','ファルコ':'元斗皇拳を使い、天帝を守る人物。'}
for w in names:
 assert w in hokuto,w
 rd={'黒夜叉':'くろやしゃ','赤鯱':'あかしゃち','牙族長':'きばぞくちょう'}.get(w,reading(w))
 add(w,rd,'『北斗の拳』の登場人物。'+hd.get(w,'ケンシロウたちの物語に登場する。'),'北斗の拳',['https://hokuto-no-ken.jp/hokuto_archives'],dict(file='hokuto-characters.html',name=w))

# Dictionary evidence is distinct from an editorial compound/genre/name review.
dictpath=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json')
dictionary=json.loads(dictpath.read_text(encoding='utf-8'));index={}
for e in dictionary['words']:
 for form in e['kanji']+e['kana']:
  if not set(form['tags'])<={'sk'}:continue
  index.setdefault(norm(form['text']),[]).append(e)
for x in pool:
 if x['category'] in ['楽器','音楽ジャンル']:
  es=index.get(norm(x['word']),[])
  es=[e for e in es if any(norm(k['text'])==x['reading'] for k in e['kana'])]
  if es:
   e=es[0];x['entryId']=e['id'];x['dictionaryEvidence']=dict(entryId=e['id'],kana=[k['text'] for k in e['kana']],senseIndexes=list(range(len(e['sense']))))
   x['sources']=['https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+str(e['id'])]+x['sources']
  # Same source entry can be a spelling alias of an already selected instrument.
  if x['word'] in ['スティールドラム','メロディオン']:x['omit']='same-instrument-alias-or-brand'

save(OUT/'candidates.json',pool);save(OUT/'exclusions.json',excluded)
save(OUT/'reservation-snapshot.json',dict(liveRows=len(live),liveSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),readings=sorted(reserved_readings),normalizedWords=sorted(reserved_words),files=sorted(set(reservation_files))))
print(json.dumps(dict(eligible=len(pool),categories=Counter(x['category'] for x in pool),excluded=Counter(x['reason'] for x in excluded)),ensure_ascii=False))
