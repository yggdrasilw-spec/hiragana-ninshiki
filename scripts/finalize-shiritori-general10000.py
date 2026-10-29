"""Freeze source-backed ordinary nouns and deliberate spelling variants before import."""
import csv,json,hashlib,re,collections,sqlite3,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/general10000';B=R/'data/dictionary-imports/2026-10-29-general10000'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
if B.with_suffix('.summary.json').exists() and json.loads(B.with_suffix('.summary.json').read_text(encoding='utf-8')).get('registered'):
 print('Already registered; keep the frozen intake and use the delivery builder for runtime changes.');raise SystemExit(0)
before=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(before.decode('utf-8-sig').splitlines()));existing={(x['reading'],x['word']) for x in old};oldread={x['reading'] for x in old}
assert len(old)==66912,'Baseline changed; regenerate candidates against the new dictionary first.'
rows=[json.loads(l) for l in (D/'candidates.jsonl').read_text(encoding='utf-8').splitlines()]
editorial={}
for line in (D/'editorial.tsv').read_text(encoding='utf-8-sig').splitlines():
 w,r,g,m=line.split('\t');editorial[(r,w)]=(int(g),m)
# Retain complete dictionary definitions. Flag regional, malformed and circular
# explanations instead of pretending an automatic check is a full lexical review.
reject=re.compile('米国|アメリカ|英国|イギリス|フランス|ギリシア|ローマカトリック|共和国|諜報機関|連邦政府|第[0-9０-９]+学年|最も危険|最も大き|世界一|出力ろ|たちち|示さた|パーティーリスト|の下位区分|であること。$')
items=[];deferred=[]
for x in rows:
 key=(x['reading'],x['word']);m=x['meaning']
 circular=m.replace('。','') in [x['word']+'する行為',x['word']+'の行為',x['word']+'をすること',x['word']+'であること',x['word']+'の状態']
 if key not in editorial and (reject.search(m) or circular):deferred.append(dict(reading=x['reading'],word=x['word'],reason='説明の地域依存・不自然さ・循環説明。個別編集待ち。'));continue
 x['grade'],x['meaning']=editorial.get(key,(4,m));x['editorial']=key in editorial
 items.append(x)
keys={(x['reading'],x['word']) for x in items};need=set(editorial)-keys-existing
jm=json.loads((D/'sources/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
def kana(t):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in t)
for e in jm['words']:
 for k in e['kana']:
  for w in e['kanji'] or [{'text':k['text']}]:
   key=(kana(k['text']),w['text'])
   if key not in need or ('*' not in k['appliesToKanji'] and w['text'] not in k['appliesToKanji']):continue
   senses=[s for s in e['sense'] if 'n' in s['partOfSpeech'] and ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) and ('*' in s['appliesToKanji'] or w['text'] in s['appliesToKanji'])]
   if not senses:continue
   g,m=editorial[key];items.append(dict(reading=key[0],word=key[1],grade=g,meaning=m,editorial=True,common=k['common'],jmdict=[dict(id=e['id'],gloss=[z['text'] for s in senses for z in s['gloss'] if z['lang']=='eng'])],alignment=[],entryId=None,senseId=None,synset=None,count=0));need.remove(key)
# No synthetic pronunciations for a missed hand-written seed.
print('unmatched editorial seeds',sorted(need))
for name in ['wordnet','jmdict']:
 src=D/'sources/wnja/LICENSE' if name=='wordnet' else None
 if src:shutil.copyfile(src,D/(name+'-LICENSE.txt'))
shutil.copyfile(D/'sources/omw-en/LICENSE',D/'english-wordnet-LICENSE.txt')
(D/'jmdict-NOTICE.md').write_text('読み・品詞・語義照合: JMdict / Electronic Dictionary Research and Development Group (EDRDG)。2026-10-05版をjmdict-simplifiedから取得。\n\nhttps://www.edrdg.org/jmdict/j_jmdict.html\nhttps://www.edrdg.org/edrdg/licence.html\nCC BY-SA 4.0: https://creativecommons.org/licenses/by-sa/4.0/\n\n採用語のID・照合した英語見出しをentries.jsonlに保持。日本語定義は日本語WordNetまたは独自編集文。\n',encoding='utf-8')
for i,x in enumerate(items,len(old)+1):
 x.update(id=i,level=1 if x['grade']==1 else 2 if x['grade']<=3 else 3,imagequery='',imagequery_en='',image_asset='',image_mode='none',image_credit='',category='一般語・別表記')
 x['source']=dict(dataset='日本語WordNet 2.1 / JMdict',title=('独自編集文。読み：JMdict' if x['editorial'] else '日本語WordNet 2.1 / JMdict'),url='https://www.edrdg.org/jmdict/j_jmdict.html' if x['editorial'] else 'https://bond-lab.github.io/wnja/jpn/downloads.html',license='JMdict CC BY-SA 4.0 / WordNet License',licenseUrl='https://www.edrdg.org/edrdg/licence.html',wordnetLicense='data/general10000/wordnet-LICENSE.txt',synset=x['synset'],jmdictIds=[j['id'] for j in x['jmdict']],modified='基本語は独自編集。その他は句点・空白のみ整形。',retrievedOn='2026-10-29')
 if x['editorial']:
  x['candidateSenseId']=x['senseId'];x['candidateSynset']=x['synset'];x['senseId']=None;x['synset']=None;x['source']['synset']=None
 x['lexicalSource']=x['source'];x['meaningReason']='基本語を個別に説明作成。' if x['editorial'] else '日本語WordNetの名詞語義。JMdictの同一表記・読み・名詞語義の英訳と英語WordNet見出しが一致。語義の全件人手校閲ではない。'
 x['ageReason']='基本的な生活語を個別編集し意味別レベル'+str(x['grade'])+'。' if x['editorial'] else '一般名詞・抽象語・別表記を広く採用。小学生向け説明の全件校閲前につきCPUは意味別レベル4以上。児童の入力は全レベルで可。'
 if x['reading'] in oldread:x['distinctSenseReason']='同じ読みの一般名詞・別表記も追加するというユーザー方針。同一の読みと表記の組は既存にない。既存の意味・画像を保持する。'
 x['imageReason']='今回は説明のみ。画像を自動検索しない。'
assert len(items)>10000 and len({(x['reading'],x['word']) for x in items})==len(items)
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
for x in items:assert not re.search('[,\r\n]',x['word']+x['meaning'])
B.with_suffix('.csv').write_text(header+'\n'+''.join(','.join(str(x[k]) for k in header.split(','))+'\n' for x in items),encoding='utf-8',newline='\n')
save(B.with_suffix('.review.json'),items)
(D/'entries.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in items),encoding='utf-8',newline='\n')
save(D/'selection-deferrals.json',deferred)
(D/'registration-baseline.csv').write_bytes(before)
sources=[]
for f in [D/'sources/wnja-2.1.tar.xz',D/'sources/jmdict-eng.json.tgz',D/'sources/omw-en-2.0.tar.xz']:
 sources.append(dict(file=f.name,sha256=sha(f.read_bytes()),bytes=f.stat().st_size))
save(D/'source-metadata.json',dict(retrievedOn='2026-10-29',sources=sources,urls=['https://github.com/bond-lab/wnja/releases/download/v2.1/wnja-2.1.tar.xz','https://github.com/scriptin/jmdict-simplified/releases/download/3.6.2%2B20261005200550/jmdict-eng-3.6.2+20261005200550.json.tgz','https://github.com/omwn/omw-data/releases/download/v2.0/omw-en-2.0.tar.xz'],limits=['全件人手校閲ではない。','自動照合は読み・品詞・英語見出しの一致であり語義の正しさの証明ではない。','別表記・別読みを収録する。同じ読みはゲーム内で一つにまとめる。']))
counts=collections.Counter(x['reading'] for x in items)
summary=dict(registered=False,baselineRows=len(old),beforeSha256=sha(before),added=len(items),newReadings=len(set(counts)-oldread),existingReadings=len(set(counts)&oldread),variantReadings=sum(n>1 for n in counts.values()),levels=dict(collections.Counter(str(x['grade']) for x in items)),editorial=sum(x['editorial'] for x in items),endingN=sum(x['reading'].endswith('ん') for x in items),explanationOnly=len(items),deferred=len(deferred))
save(B.with_suffix('.summary.json'),summary)
# Searchable management database; runtime delivery remains bounded JSON chunks.
dbpath=D/'catalog.sqlite'
if dbpath.exists():dbpath.unlink()
db=sqlite3.connect(dbpath);db.executescript('CREATE TABLE entries(id INTEGER PRIMARY KEY,reading TEXT,word TEXT,meaning TEXT,grade INTEGER,editorial INTEGER,synset TEXT,jmdict_ids TEXT); CREATE INDEX by_reading ON entries(reading); CREATE INDEX by_word ON entries(word); CREATE VIRTUAL TABLE search USING fts5(word,reading,meaning,content=entries,content_rowid=id,tokenize="trigram");')
for x in items:db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?)',(x['id'],x['reading'],x['word'],x['meaning'],x['grade'],int(x['editorial']),x['synset'],json.dumps(x['source']['jmdictIds'])))
db.execute("INSERT INTO search(search) VALUES('rebuild')");db.commit();db.close();print(json.dumps(summary,ensure_ascii=False))
