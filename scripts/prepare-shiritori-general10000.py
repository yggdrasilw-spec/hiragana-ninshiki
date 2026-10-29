import json,xml.etree.ElementTree as E,collections,re,csv,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1]; D=R/'data/general10000'; S=D/'sources'
x=E.parse(S/'wnja/wnja-2.1.xml').getroot()[0]; jm=json.loads((S/'jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
norm=lambda t:unicodedata.normalize('NFKC',t)
kana=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
baseline=(D/'registration-baseline.csv' if (D/'registration-baseline.csv').exists() else R/'whitelist.csv').read_text(encoding='utf-8-sig').splitlines()
summary=R/'data/dictionary-imports/2026-10-29-general10000.summary.json'
if summary.exists():baseline=baseline[:json.loads(summary.read_text(encoding='utf-8'))['baselineRows']+1]
old=list(csv.DictReader(baseline)); existing={(z['reading'],norm(z['word'])) for z in old}
black=[]
for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);black.append((m[1].lower(),kana(m[2])) if m else ('contains',kana(line)))
index=collections.defaultdict(list)
for e in jm['words']:
 for k in e['kana']:
  for w in e['kanji'] or [{'text':k['text'],'common':k['common']}]:
   if '*' not in k['appliesToKanji'] and w['text'] not in k['appliesToKanji']:continue
   senses=[s for s in e['sense'] if 'n' in s['partOfSpeech'] and ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) and ('*' in s['appliesToKanji'] or w['text'] in s['appliesToKanji']) and not s['dialect'] and not any(t in s['misc'] for t in ['arch','obs','rare','vulg','derog','sl','dated','sens','X']) and (not s['field'] or k['common'])]
   if senses:index[(kana(k['text']),norm(w['text']))].append(dict(id=e['id'],common=k['common'],gloss=[g['text'] for s in senses for g in s['gloss'] if g['lang']=='eng']))
en=E.parse(S/'omw-en/omw-en.xml').getroot()[0]
ensyn={s.get('id').replace('omw-en-','wnja-'):s for s in en.findall('Synset')}
english=collections.defaultdict(set)
gnorm=lambda t:re.sub(r'[^a-z0-9 ]','',re.sub(r'\([^)]*\)','',t.lower().replace('_',' '))).strip()
for e in en.findall('LexicalEntry'):
 for se in e.findall('Sense'):
  english[se.get('synset').replace('omw-en-','wnja-')].add(gnorm(e.find('Lemma').get('writtenForm')))
syn={s.get('id'):s for s in x.findall('Synset')};out={};reasons=collections.Counter()
unsafe=re.compile('性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい')
for e in x.findall('LexicalEntry'):
 l=e.find('Lemma');f=e.find("Form[@script='hira']")
 if l.get('partOfSpeech')!='n' or f is None:continue
 w=l.get('writtenForm');r=kana(f.get('writtenForm'));key=(r,norm(w))
 reason=None
 if key in existing:reason='existing-pair'
 elif not re.fullmatch('[ぁ-ゖー]{1,20}',r) or r.startswith('ん'):reason='reading-format'
 elif re.search(r'[\s,\r\n()（）/／0-9A-Za-z−-]',w):reason='word-format'
 elif key not in index:reason='no-independent-noun-reading'
 elif any(r==p if m=='exact' else p in r for m,p in black):reason='blacklist'
 if reason:reasons[reason]+=1;continue
 choices=[]
 for sense in e.findall('Sense'):
  if float(sense.get('confidenceScore','1'))<.9:continue
  s=syn.get(sense.get('synset'))
  if s is None or s.find('ILIDefinition') is not None:continue
  es=ensyn.get(sense.get('synset'))
  if es is None or es.find('SynsetRelation[@relType="instance_hypernym"]') is not None:continue
  glosses={gnorm(g) for j in index[key] for g in j['gloss']}
  aligned=glosses & english[sense.get('synset')]
  if not aligned:continue
  defs=[d.text for d in s.findall('Definition') if d.text]
  for definition in defs:
   meaning=re.sub(r'\s+',' ',definition).strip(' 。')+'。'
   if not 7<=len(meaning)<=115 or unsafe.search(w+meaning) or re.search(r'[,\r\n]|[A-Za-z]{3}|\?|？',meaning):continue
   if re.search('出力ろ入力|労働者たちち|示さた|：。|複数形|とも呼|を参照|の略|の別名|については|通常は複数形|複数形で|特に米国|古語|俗語|侮辱',meaning):continue
   counts=sum(int(c.text or 0) for c in sense.findall('Count'))
   choices.append((counts,-len(meaning),sense.get('synset'),meaning,sense.get('id')))
 if not choices:reasons['definition-or-sense-filter']+=1;continue
 best=max(choices);j=index[key];common=any(v['common'] for v in j)
 row=dict(alignment=sorted({gnorm(g) for j in index[key] for g in j['gloss']} & english[best[2]]),reading=r,word=w,meaning=best[3],entryId=e.get('id'),senseId=best[4],synset=best[2],count=best[0],common=common,jmdict=j)
 if key not in out or (row['count'],-len(row['meaning']))>(out[key]['count'],-len(out[key]['meaning'])):out[key]=row
rows=sorted(out.values(),key=lambda z:(-z['common'],-z['count'],len(z['reading']),z['reading'],z['word']))
(D/'candidates.jsonl').write_text(''.join(json.dumps(z,ensure_ascii=False)+'\n' for z in rows),encoding='utf-8')
print(json.dumps(dict(baseline=len(old),candidates=len(rows),newReadings=len({z['reading'] for z in rows}-{z['reading'] for z in old}),common=sum(z['common'] for z in rows),reasons=reasons),ensure_ascii=False))
for row in rows[:140]:print(row['reading'],row['word'],row['meaning'])
print('END SAMPLE')
for row in rows[-35:]:print(row['reading'],row['word'],row['meaning'])
