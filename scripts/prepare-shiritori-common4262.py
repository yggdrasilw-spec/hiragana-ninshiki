"""Freeze the complete common-reading scope and prepare traceable Japanese drafts."""
import collections,gzip,json,re,sys,unicodedata,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote
R=Path(__file__).resolve().parents[1];D=R/'data/vocabulary-gap/common4262'
hira=lambda s:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in unicodedata.normalize('NFKC',s))
unsafe=re.compile(r'性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい|白痴|痴呆症|精神薄弱|聾唖|\b(?:sex|sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide|narcotic|racial slur|derogatory)\b',re.I)
baddef=re.compile(r'語義[0-9０-９]|語義[一二三四]|\{\{|\}\}|を参照|参照のこと|以下同|前述|上述|対義語|の漢字表記[。.]?$|の異表記[。.]?$|の別表記[。.]?$|の表記[。.]?$|「[^」]+」に同じ')
scope=[json.loads(l) for l in (D/'scope.jsonl').open(encoding='utf-8')]
cache=D/'wiktionary-matches.json'
if not cache.exists():
 allja=collections.defaultdict(list)
 with gzip.open(R/'data/vocabulary-gap/sources/jawiktionary-20261101.jsonl.gz','rt',encoding='utf-8') as stream:
  for line in stream:
   entry=json.loads(line)
   if entry.get('lang_code')=='ja':allja[entry['word']].append(entry)
 wanted={v for x in scope for v in x['variants']}|{x['reading'] for x in scope}
 for depth in range(3):
  for word in list(wanted):
   for entry in allja.get(word,[]):
    for sense in entry.get('senses',[]):
     for target in sense.get('form_of',[])+sense.get('alt_of',[]):wanted.add(target['word'])
 cache.write_text(json.dumps({w:allja[w] for w in wanted if w in allja},ensure_ascii=False),encoding='utf-8')
wiki=json.loads(cache.read_text(encoding='utf-8'))

def definitions(word,reading,trail=(), spelling=None):
 if word in trail or len(trail)>4:return []
 result=[]
 for e in wiki.get(word,[]):
  forms=[hira(f['form']) for f in e.get('forms',[]) if 'transliteration' in f.get('tags',[]) and re.fullmatch('[ぁ-ゖァ-ヶー]+',f['form'])]
  if forms and reading not in forms:continue
  written=[f['form'] for f in e.get('forms',[]) if 'kanji' in f.get('tags',[])]
  if spelling and written and spelling not in written and word!=spelling:continue
  if e['pos'] not in {'noun','adj_noun','adj-na','adv','adverb','adj','verb','phrase','proverb','character','intj','suffix','prefix','conj'}:continue
  for n,s in enumerate(e.get('senses',[]),1):
   if set(s.get('tags',[])) & {'vulgar','derogatory','offensive','pejorative','slur'}:continue
   for target in s.get('form_of',[])+s.get('alt_of',[]):
    if re.fullmatch('[ぁ-ゖァ-ヶー]+',target['word']) and hira(target['word'])!=reading:continue
    for candidate in definitions(target['word'],reading,trail+(word,),spelling):
     result.append({**candidate,'aliasTrail':[word]+candidate.get('aliasTrail',[])})
   for gloss in s.get('glosses',[]):
    g=re.sub(r'\s+',' ',gloss).replace(',','、').strip()
    label=re.match(r'^[（(]([ぁ-ゖァ-ヶー]+)[）)]',g)
    if label and hira(label[1])!=reading:continue
    if re.search('参照|表記ゆれ|連用形|を略したもの|の省略形',g):continue
    if not 4<=len(g)<=240 or unsafe.search(g) or baddef.search(g):continue
    if re.fullmatch(re.escape(word)+r'[。.]?',g):continue
    result.append(dict(meaning=g.rstrip('。')+'。',sourceWord=word,sourceSense=n,
      source='jawiktionary',sourceUrl='https://ja.wiktionary.org/wiki/'+quote(word),
      originalDefinition=gloss,readingForms=forms,sourceTags=s.get('tags',[]),aliasTrail=[]))
 return result

out=[]
for x in scope:
 safe=[]
 for e in x['evidence']:
  for s in e['senses']:
   if not unsafe.search(x['word']+' '+' '.join(s['gloss'])):safe.append(dict(entryId=e['entryId'],**s))
 item={**x,'safeJmdictSenses':safe}
 if not safe:
  item.update(status='excluded-content',reason='出典の該当語義に、既存の内容適切性方針に抵触する内容を確認。')
 else:
  drafts=[]
  # Same reading does not imply synonymy: never borrow from unrelated surfaces.
  for w in [x['word'],x['reading']]:
   drafts.extend(definitions(w,x['reading'],spelling=x['word']))
  if drafts:
   # Prefer a direct, concise definition. Editorial review can choose another sense.
   best=min(enumerate(drafts),key=lambda t:(bool(t[1]['aliasTrail']),t[0]))[1]
   item.update(best,status='draft-source-definition')
  else:item.update(status='pending-editorial',reason='適用する語義を確認して日本語説明を個別編集する。')
 out.append(item)
(D/'drafts.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out),encoding='utf-8')
pending=[x for x in out if x['status']=='pending-editorial']
(D/'pending.tsv').write_text('\n'.join(str(x['id'])+'\t'+x['reading']+'\t'+x['word']+'\t'+' ; '.join('/'.join(s['gloss']) for s in x['safeJmdictSenses']) for x in pending)+'\n',encoding='utf-8')
(D/'draft-review.tsv').write_text('\n'.join(str(x['id'])+'\t'+x['word']+'\t'+x.get('meaning',x['status']) for x in out)+'\n',encoding='utf-8')
print(json.dumps(dict(total=len(out),statuses=collections.Counter(x['status'] for x in out)),ensure_ascii=False))
