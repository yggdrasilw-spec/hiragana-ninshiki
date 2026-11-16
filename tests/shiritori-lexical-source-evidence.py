"""Validate every imported related form against the actual upstream senses."""
import collections,csv,json,re,unicodedata,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1]
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
jm=json.loads((R/'data/general10000/sources/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
index={e['id']:e for e in jm['words']};count=0;methods={}
rows=list(csv.DictReader((R/'whitelist.csv').open(encoding='utf-8-sig')))
english=E.parse(R/'data/general10000/sources/omw-en/omw-en.xml').getroot()[0]
eng=lambda t:re.sub(r'[^a-z0-9 ]','',re.sub(r'\([^)]*\)','',t.lower().replace('_',' '))).strip()
english_synsets=collections.defaultdict(set)
for entry in english.findall('LexicalEntry'):
 for se in entry.findall('Sense'):english_synsets[eng(entry.find('Lemma').get('writtenForm'))].add(se.get('synset').replace('omw-en-','wnja-'))
ja=E.parse(R/'data/general10000/sources/wnja/wnja-2.1.xml').getroot()[0]
definitions={n.get('id'):{d.text for d in n.findall('Definition')} for n in ja.findall('Synset')}
for p in sorted((R/'data/dictionary-imports').glob('2026-11-16-related-closure*.review.json')):
 for x in json.loads(p.read_text(encoding='utf-8')):
  if x.get('withdrawn'):
   assert x['withdrawalReason'];continue
  ev=x['lexicalSource'];e=index[ev['entryId']]
  ks=[k for k in e['kana'] if hira(k['text'])==x['reading']]
  assert ks,x['word']
  assert any(norm(w['text'])==norm(x['word']) for w in e['kanji']+e['kana']),x['word']
  if x['kind']=='related-form':
   assert len(e['sense'])==1,x['word'];s=e['sense'][0]
   assert set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'}
   assert any(('*' in k['appliesToKanji'] or x['word'] in k['appliesToKanji'] or norm(k['text'])==norm(x['word'])) and ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) for k in ks)
   seed=rows[ev['seedId']-1]
   assert seed['reading']==ev['seedReading'] and seed['word']==ev['seedWord']
   if ev['method']=='identical-single-sense-gloss-set':
    target=tuple(sorted({g['text'].lower().strip() for g in s['gloss'] if g['lang']=='eng'}))
    assert tuple(ev['equivalentGlossSet'])==target
    original=index[ev['seedEntryId']]
    assert len(original['sense'])==1
    assert tuple(sorted({g['text'].lower().strip() for g in original['sense'][0]['gloss'] if g['lang']=='eng'}))==target
  elif x['kind']=='compound':
   suffix,pos=ev['rule'].rsplit('-',1);assert x['word']==ev['stem']+suffix
   assert all(stem['semanticAlignment'] for stem in ev['stemEvidence'])
   for evidence in ev['evidence']:
    s=e['sense'][evidence['senseNumber']-1]
    assert set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'}
    assert set(evidence['matchedGlosses'])<={g['text'] for g in s['gloss'] if g['lang']=='eng'}
  else:
   assert x['kind']=='wordnet-confirmed'
   s=e['sense'][ev['senseNumber']-1]
   assert set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'}
   assert ev['originalDefinition'] in definitions[ev['wordnetSynset']]
  if ev.get('englishSenseWitnesses'):
   sid=ev['wordnetSynset'];witnesses=ev['englishSenseWitnesses']
   glosses={eng(g['text']) for s in e['sense'] for g in s['gloss'] if g['lang']=='eng'}
   assert set(witnesses)<=glosses,(x['word'],'wrong JMdict entry for English witnesses')
   assert any(english_synsets[w]=={sid} for w in witnesses) or len(witnesses)>=2 and set.intersection(*(english_synsets[w] for w in witnesses))=={sid},x['word']
  methods[ev['method']]=methods.get(ev['method'],0)+1;count+=1
curated=0
for p in sorted((R/'data/dictionary-imports').glob('2026-11-16-life-family*.review.json')):
 for x in json.loads(p.read_text(encoding='utf-8')):
  assert x['evidence']
  for ev in x['evidence']:
   e=index[ev['entryId']]
   assert norm(ev['sourceWord'])==norm(x['word']) and hira(ev['sourceKana'])==x['reading']
   assert any(f['text']==ev['sourceWord'] for f in e['kanji']+e['kana'])
   k=next(k for k in e['kana'] if k['text']==ev['sourceKana'])
   assert '*' in k['appliesToKanji'] or ev['sourceWord'] in k['appliesToKanji']
   for n in ev['senseNumbers']:
    s=e['sense'][n-1]
    assert set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'}
    assert '*' in s['appliesToKana'] or ev['sourceKana'] in s['appliesToKana']
    assert '*' in s['appliesToKanji'] or ev['sourceWord'] in s['appliesToKanji']
  curated+=1
print(json.dumps(dict(passed=True,sourceCheckedSenses=count,curatedSourceChecked=curated,methods=methods),ensure_ascii=False))
