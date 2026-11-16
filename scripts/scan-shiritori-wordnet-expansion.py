"""Inspect remaining source-aligned noun senses, including missing ordinary senses."""
import collections,csv,difflib,hashlib,json,re,unicodedata,xml.etree.ElementTree as E
from pathlib import Path
from shiritori_lexical_policy import REJECT_MISC
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion';S=R/'data/general10000/sources'
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
gnorm=lambda t:re.sub(r'[^a-z0-9 ]','',re.sub(r'\([^)]*\)','',t.lower().replace('_',' '))).strip()
def main():
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
 bypair=collections.defaultdict(list)
 for r in old:bypair[(r['reading'],norm(r['word']))].append(r['meaning'])
 covered=set()
 for line in (R/'data/general10000/entries.jsonl').read_text(encoding='utf-8').splitlines():
  x=json.loads(line)
  for sid in [x.get('synset'),x.get('candidateSynset')]:
   if sid:covered.add((x['reading'],norm(x['word']),sid))
 jm=json.loads((S/'jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
 index=collections.defaultdict(list)
 unsafe=re.compile(r'性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい|\b(?:sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide)\b',re.I)
 blocked=[]
 for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);blocked.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
 for e in jm['words']:
  for k in e['kana']:
   if 'ok' in k.get('tags',[]):continue
   for w in e['kanji'] or [{'text':k['text'],'common':k['common'],'tags':[]}]:
    if '*' not in k['appliesToKanji'] and w['text'] not in k['appliesToKanji']:continue
    senses=[(i,s) for i,s in enumerate(e['sense'],1) if set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'} and ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) and ('*' in s['appliesToKanji'] or w['text'] in s['appliesToKanji']) and not set(s['misc']) & REJECT_MISC]
    for i,s in senses:
     gs=[g['text'] for g in s['gloss'] if g['lang']=='eng']
     if not unsafe.search(w['text']+' '.join(gs)):index[(hira(k['text']),norm(w['text']))].append(dict(id=e['id'],senseNumber=i,common=k['common'] or w['common'],gloss=gs))
 x=E.parse(S/'wnja/wnja-2.1.xml').getroot()[0];en=E.parse(S/'omw-en/omw-en.xml').getroot()[0]
 syn={s.get('id'):s for s in x.findall('Synset')};ensyn={s.get('id').replace('omw-en-','wnja-'):s for s in en.findall('Synset')};english=collections.defaultdict(set)
 for e in en.findall('LexicalEntry'):
  for s in e.findall('Sense'):english[s.get('synset').replace('omw-en-','wnja-')].add(gnorm(e.find('Lemma').get('writtenForm')))
 reasons=collections.Counter();out={}
 for e in x.findall('LexicalEntry'):
  l=e.find('Lemma');f=e.find("Form[@script='hira']")
  if l.get('partOfSpeech')!='n' or f is None:continue
  word=l.get('writtenForm');reading=hira(f.get('writtenForm'));key=(reading,norm(word))
  if not re.fullmatch('[ぁ-ゖー]{1,120}',reading) or re.search(r'[,\r\n<>]',word):continue
  if key not in index:continue
  if any(reading==p if m=='exact' else p in reading for m,p in blocked):continue
  for se in e.findall('Sense'):
   sid=se.get('synset');s=syn.get(sid);es=ensyn.get(sid)
   if (reading,norm(word),sid) in covered:reasons['previously-covered-source-sense']+=1;continue
   if float(se.get('confidenceScore','1'))<.9 or s is None or es is None:continue
   if es.find('SynsetRelation[@relType="instance_hypernym"]') is not None:continue
   evidence=[]
   for j in index[key]:
    aligned={gnorm(g) for g in j['gloss']} & english[sid]
    if aligned:evidence.append(dict(entryId=j['id'],senseNumber=j['senseNumber'],alignedEnglish=sorted(aligned),common=j['common']))
   if not evidence:reasons['no-exact-english-sense-alignment']+=1;continue
   for definition in s.findall('Definition'):
    if not definition.text:continue
    original=definition.text;meaning=re.sub(r'\s+',' ',original).strip(' 。')+'。'
    if not 7<=len(meaning)<=140 or unsafe.search(word+meaning) or re.search(r'[,\r\n]|[A-Za-z]{3}|\?|？',meaning):continue
    if re.search('出力ろ入力|労働者たちち|示さた|：。|複数形|とも呼|を参照|の略|の別名|については|通常は複数形|特に米国|古語|俗語|侮辱',meaning):continue
    if any(meaning==m or difflib.SequenceMatcher(None,meaning,m).ratio()>.7 for m in bypair.get(key,[])):reasons['near-existing-description']+=1;continue
    candidate=dict(reading=reading,word=word,meaning=meaning,originalDefinition=original,synset=sid,senseId=se.get('id'),wordnetEntryId=e.get('id'),
     common=any(j['common'] for j in evidence),count=sum(int(c.text or 0) for c in se.findall('Count')),evidence=evidence,
     gap='additional-source-sense' if key in bypair else 'new-pair',existingMeanings=bypair.get(key,[]),relatedSynsets=[dict(target=z.get('target'),relation=z.get('relType')) for z in s.findall('SynsetRelation')],
     reviewStatus='source-aligned-provisional')
    out[(reading,norm(word),sid)]=candidate
 rows=sorted(out.values(),key=lambda z:(not z['common'],z['gap']!='new-pair',-z['count'],len(z['reading']),z['reading'],z['synset']))
 (D/'wordnet-candidates.jsonl').write_text(''.join(json.dumps(z,ensure_ascii=False)+'\n' for z in rows),encoding='utf-8')
 print(json.dumps(dict(baselineSha256=hashlib.sha256(raw).hexdigest(),candidates=len(rows),common=sum(x['common'] for x in rows),gaps=dict(collections.Counter(x['gap'] for x in rows)),reasons=reasons),ensure_ascii=False))
 for row in rows[:120]:print(row['word'],row['reading'],row['gap'],row['meaning'])
if __name__=='__main__':main()
