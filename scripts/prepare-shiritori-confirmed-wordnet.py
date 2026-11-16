"""Admit difficult nouns with independently disambiguated bilingual senses.

Difficulty, age of the word and dialect are not exclusion criteria. An English
homograph alone cannot establish that a Japanese definition belongs to a word.
"""
import collections,csv,hashlib,json,re,unicodedata,xml.etree.ElementTree as E
from pathlib import Path
from shiritori_lexical_policy import REJECT_MISC,context_notes
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion';S=R/'data/general10000/sources'
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
eng=lambda t:re.sub(r'[^a-z0-9 ]','',re.sub(r'\([^)]*\)','',t.lower().replace('_',' '))).strip()
def main():
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()));pairs={(x['reading'],norm(x['word'])) for x in old};readings={x['reading'] for x in old}
 jm=json.loads((S/'jmdict-eng-3.6.2.json').read_text(encoding='utf-8'));index=collections.defaultdict(list)
 unsafe=re.compile(r'性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい|白痴|痴呆症|精神薄弱|聾唖|\b(?:sex|sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide)\b',re.I)
 blocks=[]
 for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);blocks.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
 for e in jm['words']:
  for k in e['kana']:
   if set(k['tags']) & {'ik','ok'}:continue
   reading=hira(k['text'])
   if not re.fullmatch('[ぁ-ゖー]{1,120}',reading) or any(reading==p if mode=='exact' else p in reading for mode,p in blocks):continue
   for w in e['kanji'] or [dict(text=k['text'],tags=[])]:
    if set(w['tags']) & {'iK','ik'}:continue
    if '*' not in k['appliesToKanji'] and w['text'] not in k['appliesToKanji']:continue
    key=(reading,norm(w['text']))
    if key in pairs:continue
    for i,s in enumerate(e['sense'],1):
     if not set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'} or set(s['misc']) & REJECT_MISC:continue
     if '*' not in s['appliesToKana'] and k['text'] not in s['appliesToKana']:continue
     if '*' not in s['appliesToKanji'] and w['text'] not in s['appliesToKanji']:continue
     gloss=[g['text'] for g in s['gloss'] if g['lang']=='eng']
     if unsafe.search(w['text']+' '.join(gloss)):continue
     index[key].append(dict(entryId=e['id'],senseNumber=i,gloss=gloss,contextNote=context_notes(s,w.get('tags',[]),k.get('tags',[])),misc=s['misc'],dialect=s['dialect'],field=s['field']))
 wx=E.parse(S/'wnja/wnja-2.1.xml').getroot()[0];en=E.parse(S/'omw-en/omw-en.xml').getroot()[0]
 ws={x.get('id'):x for x in wx.findall('Synset')};es={x.get('id').replace('omw-en-','wnja-'):x for x in en.findall('Synset')};em=collections.defaultdict(set)
 for e in en.findall('LexicalEntry'):
  text=eng(e.find('Lemma').get('writtenForm'))
  for sense in e.findall('Sense'):em[text].add(sense.get('synset').replace('omw-en-','wnja-'))
 fixes=json.loads((D/'seed-description-fixes.json').read_text(encoding='utf-8'));out={};counts=collections.Counter()
 genres={'chem':'chemistry','physics':'physics','biol':'biology','geol':'earthScience','bot':'plant','zool':'animal','med':'body','ling':'school','comp':'technology','math':'school','food':'food','music':'arts'}
 for e in wx.findall('LexicalEntry'):
  lemma=e.find('Lemma');f=e.find("Form[@script='hira']")
  if lemma.get('partOfSpeech')!='n' or f is None:continue
  word=lemma.get('writtenForm');reading=hira(f.get('writtenForm'));key=(reading,norm(word))
  if key not in index or key in out or unsafe.search(word) or re.search(r'[,\r\n\t<>]',word):continue
  if word in fixes['holdWords']:continue
  choices=[]
  for sense in e.findall('Sense'):
   sid=sense.get('synset');node=ws[sid];english=es.get(sid)
   if float(sense.get('confidenceScore','1'))<.9 or english is None:continue
   if english.find('SynsetRelation[@relType="instance_hypernym"]') is not None:continue
   for j in index[key]:
    aligned={eng(g) for g in j['gloss'] if sid in em.get(eng(g),set())}
    witnesses=[g for g in aligned if em[g]=={sid}]
    if not witnesses and len(aligned)>=2:
     if set.intersection(*(em[g] for g in aligned))=={sid}:witnesses=sorted(aligned)
    if not witnesses:counts['ambiguous-english-sense']+=1;continue
    for definition in node.findall('Definition'):
     if not definition.text:continue
     original=definition.text;meaning=re.sub(r'\s+',' ',original).strip(' 。')
     meaning=re.sub(r'(?<=\d),(?=\d{3}(?:\D|$))','',meaning).replace(',','、')+'。'
     if not 7<=len(meaning)<=400 or unsafe.search(meaning) or re.search(r'\?|？|精神病院|患者の多く|知性が通常より劣る|知能が劣|出力ろ入力|労働者たちち|示さた|：。',meaning):continue
     if re.search('複数形|を参照|については|通常は複数形',meaning):continue
     if re.fullmatch(re.escape(word)+r'(?:を|が)?(?:する|である|になる)?(?:行為|こと)。',meaning):counts['circular-definition']+=1;continue
     if re.search(r'第[0-9]+学年|前置詞|米国憲法修正第',meaning):counts['regional-definition-needs-editing']+=1;continue
     meaning=fixes['overrides'].get(word,meaning)
     score=sum(int(c.text or 0) for c in sense.findall('Count'))
     choices.append((score,-len(meaning),j,sid,sense.get('id'),original,meaning,sorted(witnesses)))
  if not choices:continue
  best=max(choices,key=lambda c:(c[0],c[1]));_,_,j,sid,se,original,meaning,witnesses=best
  if j['contextNote'] and not meaning.startswith(j['contextNote']):meaning=j['contextNote']+meaning
  genre=next((genres[f] for f in j['field'] if f in genres),'other')
  out[key]=dict(kind='wordnet-confirmed',reading=reading,word=word,meaning=meaning,entryId=j['entryId'],senseNumber=j['senseNumber'],
   wordnetSynset=sid,wordnetSenseId=se,originalDefinition=original,englishSenseWitnesses=witnesses,contextNote=j['contextNote'],senseTags=j['misc'],dialectTags=j['dialect'],genre=genre,
   gap='new-reading' if reading not in readings else 'new-spelling',grade=4,definitionAuthor='日本語WordNetの定義。空白・句読点を整形。一部は独自編集。',editorialOverride=word in fixes['overrides'],reviewStatus='source-checked-provisional')
 rows=sorted(out.values(),key=lambda x:(x['gap']!='new-reading',len(x['reading']),x['reading'],x['word']))
 (D/'wordnet-confirmed-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 print(json.dumps(dict(candidates=len(rows),newReadings=len({x['reading'] for x in rows}-readings),counts=counts,baselineSha256=hashlib.sha256(raw).hexdigest()),ensure_ascii=False))
 for x in rows[:80]:print(x['word'],x['reading'],x['meaning'])
if __name__=='__main__':main()
