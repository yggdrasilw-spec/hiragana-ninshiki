"""Prepare the glossary batch; retain genuine spelling/name variants."""
import csv,json,hashlib,collections,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-28-glossary'
SOURCE=ROOT/'data/dictionary-imports/glossary-sources'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def hira(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s if c not in '・＝= 　-')
assert not (BASE.with_suffix('.summary.json').exists() and read(BASE.with_suffix('.summary.json')).get('registered')),'Already registered'
raw=(ROOT/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8').splitlines()))
by=collections.defaultdict(list);readingRows=collections.defaultdict(list)
for i,x in enumerate(old,1):
 by[(x['reading'],x['word'])].append(dict(id=i,**x));readingRows[x['reading']].append(x)
dictionaryPath=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json')
dictionary=read(dictionaryPath);forms=collections.defaultdict(list)
for e in dictionary['words']:
 for k in e['kanji']+e['kana']:
  for r in e['kana']:
   if '*' in r['appliesToKanji'] or k['text'] in r['appliesToKanji'] or k in e['kana']:
    forms[k['text']].append((hira(r['text']),e['id']))
references={
 '倫理':['https://www.shimizushoin.co.jp/books/view/727','https://www.yozemi.ac.jp/course/kouza/pdf/eth_2025.pdf','https://plato.stanford.edu/contents.html'],
 '情報':['https://www.mext.go.jp/a_menu/shotou/zyouhou/detail/1416756.htm','https://sites.google.com/a.ipsj.or.jp/ipsjjn/resources/wordlist-v2','https://www.ipa.go.jp/shiken/asia/qv6pgp0000002s9q-att/000027072.pdf'],
 '古典':['https://www.mext.go.jp/content/20250410-mxt_kyoiku01-100002620_02.pdf','https://tbqr.sanseido-publ.co.jp/09-seisenkoten/contents/koten-bunpo-list/']}
# These are actual separate senses, not a rewording of the pre-existing sense.
special=set('パース アッシュ ブーバー オルテガ コスモス カオス 愛 調節 労働 仕事 活動 砂漠 牧場 帝国主義 好き 頼む 情け まもる ループ グラフ クラス レコード 結合 選択 インデックス 範囲 分類 ネスト 正直 昇華 投射 同化 気 反省 感覚 観察 仮説 立法 不安 抵抗 持続 復活 アトム カウンタ'.split())
items=[];excluded=[];pairSenses=collections.defaultdict(list);candidates=[]
category=''
for line in BASE.with_suffix('.authored.tsv').read_text(encoding='utf-8').splitlines():
 if '|' not in line:category=line;continue
 r,w,m=line.split('|');candidates.append(dict(reading=r,word=w,meaning=m,category=category,origin='editorial'))
overrides=dict(MECE='みーしー',PERT='ぱーと',ANSI='あんしー',IEEE='あいとりぷるいー',JIS='じす',MOOC='むーく',GB='ぎがばいと',KB='きろばいと',MB='めがばいと',PB='ぺたばいと',TB='てらばいと',HEIF='ひーふ',RAW='ろー',TIFF='てぃふ',MIDI='みでぃ',FLAC='ふらっく',WAVE='うぇーぶ',MPEG='えむぺぐ',ZIP='じっぷ',LATCH='らっち',ENIAC='えにあっく',MIPS='みっぷす',TRON='とろん',AND='あんど',EOR='いーおあ',XOR='えっくすおあ',NOT='のっと',OR='おあ',JAVA='じゃば',CAD='きゃど',NAPT='なぷと',NAT='なっと',ICANN='あいきゃん',NIC='にっく',PIN='ぴん',RAT='らっと',JSON='じぇいそん',VUCA='ぶーか',RESAS='りーさす',CHAR='ちゃー',CODE='こーど',CORREL='これる',IF='いふ',MAX='まっくす',MEDIAN='めでぃあん',MIN='みん',RAND='らんど',SUM='さむ')
sourceRows=list(csv.DictReader((SOURCE/'ipsj-wordlist.csv').open(encoding='utf-8-sig')))
for x in read(SOURCE/'ipsj-selected.json'):
 w=x['word'];r=overrides.get(w,x['reading']);m=x['meaning'].replace('|','｜')
 if not m.endswith(('。','.','！','？')):m+='。'
 candidates.append(dict(reading=r,word=w,meaning=m,category='情報／'+x['category'],origin='ipsj',sourceRow=x['sourceRow'],readingMethod='editorial-standard-pronunciation' if w in overrides else x['readingMethod']))
for c in candidates:
 r,w,m=hira(c['reading']),c['word'],c['meaning'];c['reading']=r;pair=(r,w);cat=c['category'];area=cat.split('／')[0]
 assert re.fullmatch('[ぁ-ゖー]+',r),(r,w)
 assert not any(ch in w+m for ch in ',\n\r|'),w
 assert 4<=len(m)<=260,(w,len(m))
 existing=by.get(pair,[]);previous=pairSenses[pair]
 book='著作' in cat
 separate=bool(w in special or book)
 if any(x['meaning']==m for x in existing+previous):reason='exact-entry-already-present'
 elif existing and book and w not in {'国家','告白','リヴァイアサン','帝国主義','プラグマティズム','風土','神の国'}:reason='same-title-already-present'
 elif existing and not separate:reason='same-word-and-reading-already-present'
 elif previous and not (book or (area!=previous[0]['category'].split('／')[0] and c['origin']=='editorial')):reason='same-candidate-sense-already-present'
 elif existing and book and any(any(n in x['meaning'] for n in re.findall('([一-龠ァ-ヶー・＝]{2,})の(?:著作|作品|対話篇|説話集)',m)) for x in existing):reason='same-book-already-present'
 else:reason=None
 if reason:excluded.append(dict(**c,reason=reason,existingIds=[x['id'] for x in existing]));continue
 ids=sorted({eid for kana,eid in forms.get(w,[]) if kana==r})
 lexical=dict(method='JMdictによる語形・読み一致。語義は別途確認。' if ids else '標準的な人名・思想・用語・別表記として編集確認。辞書見出し一致とは区別。',references=references[area],dictionaryEntryIds=ids)
 if c['origin']=='ipsj':
  source=sourceRows[c['sourceRow']-2]
  assert w in [t.strip() for t in source['用語'].split('|')],w
  lexical.update(method='情報処理学会の公開用語リストの掲載語・説明を使用。読みを別途照合。',sourceRow=c['sourceRow'],sourceGroup=source['用語'],license='CC BY-SA 4.0',attribution='情報処理学会 情報入試委員会「情報科全教科書用語リスト第2版」2026-10-13',definitionTransform='改行を空白に、半角カンマを読点に変換。注番号を除去。必要に応じ句点を付与。',readingMethod=c['readingMethod'])
 x=dict(id=len(old)+len(items)+1,reading=r,word=w,meaning=m,imagequery=w,level='3',imagequery_en='',image_asset='',image_mode='none',image_credit='',grade=5,category=cat,origin=c['origin'],lexicalSource=lexical,
  meaningReason=('公開ライセンスの説明を科目用語の意味として採用。' if c['origin']=='ipsj' else '専門語義・人物・著作・別表記を区別し短文を独自作成。')+m,
  ageReason='高校'+area+'の用語集相当の専門的な語義として「はってん」に配置。',imageReason='今回の追加は説明のみ。外部画像検索も行わない。')
 hom=readingRows[r]
 if hom:x['distinctSenseReason']='読みが同じ既存項目とは表示語・語義を区別する。正式名・別名・表記の揺れも独立した入力語として登録。今回の意味は「'+m+'」。'
 items.append(x);pairSenses[pair].append(x);readingRows[r].append(x)
header=raw.decode('utf-8').splitlines()[0].split(',')
with BASE.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
 f.write(','.join(header)+'\n')
 for x in items:f.write(','.join(str(x[k]) for k in header)+'\n')
save(BASE.with_suffix('.review.json'),items);save(BASE.with_suffix('.excluded.json'),excluded)
summary=dict(registered=False,baselineRows=len(old),beforeSha256=sha(raw),added=len(items),areas=dict(collections.Counter(x['category'].split('／')[0] for x in items)),categories=dict(collections.Counter(x['category'] for x in items)),newReadings=len({x['reading'] for x in items}-{x['reading'] for x in old}),endingN=sum(x['reading'].endswith('ん') for x in items),dictionaryFormMatches=sum(bool(x['lexicalSource']['dictionaryEntryIds']) for x in items),sourceCounts=dict(collections.Counter(x['origin'] for x in items)),explanationOnly=len(items))
save(BASE.with_suffix('.summary.json'),summary)
save(BASE.with_suffix('.sources.json'),dict(retrievedOn='2026-10-28',references=references,ipsj=dict(url='https://sites.google.com/a.ipsj.or.jp/ipsjjn/resources/wordlist-v2',exportUrl='https://docs.google.com/spreadsheets/d/1FYsq1-ZmwrovR1j8_Q_M5QmSlj6NIZdy/export?format=csv',file=str((SOURCE/'ipsj-wordlist.csv').relative_to(ROOT)).replace('\\','/'),sha256=sha((SOURCE/'ipsj-wordlist.csv').read_bytes()),rows=len(sourceRows),describedRows=sum(bool(x['説明'].strip()) for x in sourceRows),license='CC BY-SA 4.0',licenseUrl='https://creativecommons.org/licenses/by-sa/4.0/'),jmdict=dict(date=dictionary['dictDate'],version=dictionary['version'],sha256=sha(dictionaryPath.read_bytes()),attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',url='https://www.edrdg.org/edrdg/licence.html'),policy='人名の姓名・通称・漢訳名、概念の同義名や異なる表記も保持。完全に同じ入力・表示・語義の再追加はしない。高校用語の分野別選定であり市販用語集の全索引の照合や全語義の網羅ではない。'))
print(json.dumps(summary,ensure_ascii=False))
