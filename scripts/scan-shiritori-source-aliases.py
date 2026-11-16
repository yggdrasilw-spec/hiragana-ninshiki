"""Meaning-scoped related-form expansion. Never equate homophones by reading."""
import collections,csv,difflib,hashlib,json,re,subprocess,unicodedata,xml.etree.ElementTree as E
from pathlib import Path
from shiritori_lexical_policy import REJECT_MISC, context_notes
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion';S=R/'data/general10000/sources'
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
def main():
 subprocess.run(['node','-e',"const fs=require('fs'),vm=require('vm'),c=vm.createContext({});c.window=c;vm.runInContext(fs.readFileSync('shiritori-vocabulary.js','utf8'),c);const s=require('./scripts/shiritori-named-senses.cjs'),named=s.load(process.cwd()),reviewed=s.loadReviewedGeneral(process.cwd());const keys=[];for(const line of fs.readFileSync('whitelist.csv','utf8').trimEnd().split('\\n').slice(1)){const [reading,word,meaning]=line.split(','),key=[reading,word,meaning].join('\\t');if(!reviewed.has(key)&&(named.has(key)||c.ShiritoriVocabulary.isNamedSense(word,meaning)))keys.push(key)}fs.writeFileSync('data/lexical-expansion/named-seed-exclusions.json',JSON.stringify(keys));"],cwd=R,check=True)
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
 pairs={(r['reading'],norm(r['word'])) for r in old};readings={r['reading'] for r in old}
 for file in (R/'data/dictionary-imports').glob('2026-11-16-related-closure*.held.json'):
  for x in json.loads(file.read_text(encoding='utf-8')):
   if '廃止済み' in x.get('reason',''):pairs.add((x['reading'],norm(x['word'])))
 bykey={(r['reading'],r['word'],r['meaning']):i+1 for i,r in enumerate(old)}
 seeds=collections.defaultdict(list)
 en=E.parse(S/'omw-en/omw-en.xml').getroot()[0]
 english_synsets=collections.defaultdict(set)
 normalize_english=lambda t:re.sub(r'[^a-z0-9 ]','',re.sub(r'\([^)]*\)','',t.lower().replace('_',' '))).strip()
 for entry in en.findall('LexicalEntry'):
  lemma=normalize_english(entry.find('Lemma').get('writtenForm'))
  for se in entry.findall('Sense'):english_synsets[lemma].add(se.get('synset').replace('omw-en-','wnja-'))
 machine_wordnet_ids=set()
 for line in (R/'data/general10000/entries.jsonl').read_text(encoding='utf-8').splitlines():
  x=json.loads(line);key=(x['reading'],x['word'],x['meaning'])
  if key not in bykey:continue
  editorial=x.get('editorial',False);proof=[]
  if not editorial:
   machine_wordnet_ids.add(bykey[key]);sid=x.get('synset')
   aligned=x.get('alignment',[])
   proof=[g for g in aligned if english_synsets.get(g)=={sid}]
   if not proof and len(aligned)>=2:
    possible=set.intersection(*(english_synsets.get(g,set()) for g in aligned))
    if possible=={sid}:proof=list(aligned)
   # A hard term is admissible. An ambiguous English homograph is not evidence
   # that its Japanese reading denotes the same sense (baby/project, etc.).
   if not proof:continue
  for entry in x['jmdict']:
   scoped_proof=proof
   if not editorial:
    # A reading/form can belong to several JMdict entries. Bind the English
    # witnesses to this exact entry, not to a neighbouring entry's meaning.
    available={normalize_english(g) for g in entry['gloss']}
    local_aligned=[g for g in aligned if g in available and sid in english_synsets.get(g,set())]
    scoped_proof=[g for g in local_aligned if english_synsets[g]=={sid}]
    if not scoped_proof and len(local_aligned)>=2:
     if set.intersection(*(english_synsets[g] for g in local_aligned))=={sid}:scoped_proof=local_aligned
    if not scoped_proof:continue
   seed=dict(id=bykey[key],reading=x['reading'],word=x['word'],meaning=x['meaning'],grade=x['grade'],source=x['source'],editorial=editorial)
   if not editorial:seed.update(sameEntryOnly=True,wordnetSynset=x['synset'],englishSenseWitnesses=scoped_proof)
   seeds[str(entry['id'])].append(seed)
 for file in sorted((R/'data/dictionary-imports').glob('2026-11-16-life-family*.review.json')):
  for x in json.loads(file.read_text(encoding='utf-8')):
   for e in x['evidence']:seeds[e['entryId']].append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],grade=x['grade'],source=dict(title='JMdict・独自説明',url=e['url'],license='CC BY-SA 4.0'),editorial=True))
 for file in sorted((R/'data/dictionary-imports').glob('2026-11-16-related-closure*.review.json')):
  for x in json.loads(file.read_text(encoding='utf-8')):
   if x.get('kind')!='compound':continue
   if (x['reading'],x['word'],x['meaning']) not in bykey:continue
   eid=x['lexicalSource']['entryId']
   seeds[eid].append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],grade=4,
    source=dict(title='JMdict・複合語の構造説明',url='https://www.edrdg.org/jmdict/j_jmdict.html',license='CC BY-SA 4.0'),editorial=False,sameEntryOnly=True))
 jm=json.loads((S/'jmdict-eng-3.6.2.json').read_text(encoding='utf-8'));out={};counts=collections.Counter()
 fixes=json.loads((D/'seed-description-fixes.json').read_text(encoding='utf-8'))
 named=set(json.loads((D/'named-seed-exclusions.json').read_text(encoding='utf-8')))
 trusted={x['id'] for ss in seeds.values() for x in ss if x['editorial']}
 grades={x['id']:x['level'] for x in json.loads((R/'data/shiritori-grade-review.json').read_text(encoding='utf-8'))}
 pair_entries=collections.defaultdict(set)
 # Independent Japanese definitions are a second check on inherited meaning.
 wx=E.parse(S/'wnja/wnja-2.1.xml').getroot()[0]
 ws={s.get('id'):s for s in wx.findall('Synset')};wd=collections.defaultdict(list)
 for entry in wx.findall('LexicalEntry'):
  lemma=entry.find('Lemma');f=entry.find("Form[@script='hira']")
  if lemma.get('partOfSpeech')!='n' or f is None:continue
  key=(hira(f.get('writtenForm')),norm(lemma.get('writtenForm')))
  for se in entry.findall('Sense'):
   if float(se.get('confidenceScore','1'))<.9:continue
   for definition in ws[se.get('synset')].findall('Definition'):
    if definition.text:wd[key].append(dict(synset=se.get('synset'),definition=definition.text))
 def content(t):
  t=re.sub(r'[\s。、;；（）()・]','',t)
  for stop in ['という','である','として','ための','ために','すること','こと','もの','など','できる','している','ている','いる','ある','また','使う','つかう']:
   t=t.replace(stop,'')
  return t
 def agrees(text,definition):
  a,b=content(text),content(definition)
  aa={a[i:i+3] for i in range(len(a)-2)};bb={b[i:i+3] for i in range(len(b)-2)}
  return len(aa&bb)>=2 and (len(aa&bb)/max(1,min(len(aa),len(bb)))>=.20 or difflib.SequenceMatcher(None,a,b).find_longest_match().size>=7)
 held=[]
 for e in jm['words']:
  for k in e['kana']:
   for w in e['kanji'] or [dict(text=k['text'])]:
    if '*' in k['appliesToKanji'] or w['text'] in k['appliesToKanji']:pair_entries[(hira(k['text']),norm(w['text']))].add(e['id'])
 manual_by_pair=collections.defaultdict(list)
 for i,x in enumerate(old,1):
  if i in machine_wordnet_ids:continue
  if len(pair_entries[(x['reading'],norm(x['word']))])!=1:continue
  if '\t'.join([x['reading'],x['word'],x['meaning']]) in named:continue
  if not 7<=len(x['meaning'])<=400:continue
  if re.search(r'キャラクター|アニメ「|漫画「|作品名|楽曲名|アルバム名|グループ名|選手名|ブランド名|商品名|企業名|会社名|映画作品|テレビ番組|ポケモンの',x['meaning']):continue
  manual_by_pair[(x['reading'],norm(x['word']))].append(dict(id=i,reading=x['reading'],word=x['word'],meaning=x['meaning'],grade=grades[i],
   source=dict(title='既存の説明 / JMdict見出し照合',url='https://www.edrdg.org/jmdict/j_jmdict.html',license='CC BY-SA 4.0'),editorial=grades[i]<=3,sameReadingOnly=True,sameEntryOnly=grades[i]>3))
 for e in jm['words']:
  if len(e['sense'])!=1:continue
  for k in e['kana']:
   for w in e['kanji'] or [dict(text=k['text'])]:
    if '*' not in k['appliesToKanji'] and w['text'] not in k['appliesToKanji']:continue
    seeds[e['id']].extend(manual_by_pair.get((hira(k['text']),norm(w['text'])),[]))
 forbidden=REJECT_MISC
 unsafe=re.compile(r'性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい|\b(?:sex|sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide)\b',re.I)
 blocked=[]
 for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);blocked.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
 def signature(e):
  if len(e['sense'])!=1:return None
  s=e['sense'][0]
  if not set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'} or set(s['misc']) & forbidden:return None
  gs=tuple(sorted({g['text'].lower().strip() for g in s['gloss'] if g['lang']=='eng'}))
  if not gs or unsafe.search(' '.join(gs)):return None
  # A lone English polyseme (e.g. baby, lead) cannot establish equivalence.
  if len(gs)==1 and (len(gs[0])<8 or ' ' not in gs[0]):return None
  return gs
 semantic=collections.defaultdict(list)
 for e in jm['words']:
  sig=signature(e)
  if sig is None:continue
  for seed in seeds.get(e['id'],[]):
   if seed.get('sameEntryOnly'):continue
   if not any(hira(k['text'])==seed['reading'] and ('*' in k['appliesToKanji'] or seed['word'] in k['appliesToKanji']) for k in e['kana']):continue
   if e['kanji'] and not any(norm(w['text'])==norm(seed['word']) for w in e['kanji']):continue
   if unsafe.search(seed['word']+seed['meaning']):continue
   semantic[sig].append(dict(**seed,seedEntryId=e['id']))
 for e in jm['words']:
  sig=signature(e)
  if sig is None or e['id'] in seeds and seeds[e['id']]:continue
  for seed in semantic.get(sig,[]):
   if seed['seedEntryId']==e['id']:continue
   inherited={k:v for k,v in seed.items() if k!='sameReadingOnly'}
   inherited['equivalentGlossSet']=list(sig)
   seeds[e['id']].append(inherited)
 for e in jm['words']:
  if e['id'] not in seeds:continue
  # A single independent noun sense avoids propagating one homograph's
  # definition to another meaning within the same dictionary entry.
  if len(e['sense'])!=1:counts['multiple-senses-held']+=1;continue
  sense=e['sense'][0]
  if not set(sense['partOfSpeech']) & {'n','n-t','n-adv','n-vs'} or set(sense['misc']) & forbidden:continue
  if unsafe.search(' '.join(g['text'] for g in sense['gloss'])):continue
  valid=[]
  for seed in seeds[e['id']]:
   if seed.get('equivalentGlossSet'):
    if signature(e)!=tuple(seed['equivalentGlossSet']):continue
    valid.append(seed);continue
   if not any(hira(k['text'])==seed['reading'] and ('*' in sense['appliesToKana'] or k['text'] in sense['appliesToKana']) and ('*' in k['appliesToKanji'] or seed['word'] in k['appliesToKanji']) for k in e['kana']):continue
   if e['kanji'] and not any(norm(w['text'])==norm(seed['word']) for w in e['kanji']):continue
   if '*' not in sense['appliesToKanji'] and seed['word'] not in sense['appliesToKanji']:continue
   if unsafe.search(seed['word']+seed['meaning']):continue
   if re.search(r'米国|米国の|イギリスで|英国で|特に米国|を参照|とも呼|については|^[^。]{0,20}する行為。$',seed['meaning']):continue
   valid.append(seed)
  if not valid:continue
  seed=min(valid,key=lambda x:(not x['editorial'],x['grade'],x['id']))
  if seed['word'] in fixes['holdWords']:
   counts['seed-description-needs-correction']+=1
   held.append(dict(entryId=e['id'],seedId=seed['id'],seedWord=seed['word'],reason=fixes['holdWords'][seed['word']]))
   continue
  checks=[]
  if seed['id'] not in trusted:
   if re.search(r'伯父|叔父|伯母|叔母',seed['word']):
    counts['kinship-specific-definition-held']+=1;continue
   for k in e['kana']:
    for w in e['kanji'] or [dict(text=k['text'])]:
     if '*' in k['appliesToKanji'] or w['text'] in k['appliesToKanji']:
      checks.extend(d for d in wd.get((hira(k['text']),norm(w['text'])),[]) if agrees(seed['meaning'],d['definition']))
   if not checks and seed.get('equivalentGlossSet'):
    counts['no-independent-japanese-meaning-consensus']+=1
    held.append(dict(entryId=e['id'],seedId=seed['id'],seedWord=seed['word'],reason='既存説明と独立した日本語定義の意味一致を機械確認できない。個別編集待ち。'))
    continue
  for k in e['kana']:
   if set(k['tags']) & {'ik','ok'}:continue
   reading=hira(k['text'])
   if seed.get('sameReadingOnly') and reading!=seed['reading']:continue
   if not re.fullmatch('[ぁ-ゖー]{1,120}',reading):continue
   if any(reading==p if mode=='exact' else p in reading for mode,p in blocked):continue
   if '*' not in sense['appliesToKana'] and k['text'] not in sense['appliesToKana']:continue
   # The kana headword itself is a legitimate written form; it retains the
   # applicable reading and is not generated by combining arbitrary spellings.
   forms=e['kanji']+[dict(text=k['text'],tags=[])]
   for w in forms:
    word=w['text'];key=(reading,norm(word))
    if key in pairs:continue
    if set(w['tags']) & {'iK','ik'}:continue
    if '*' not in k['appliesToKanji'] and word not in k['appliesToKanji']:
     if word!=k['text']:continue
    if '*' not in sense['appliesToKanji'] and word not in sense['appliesToKanji']:
     if word!=k['text']:continue
    if re.search(r'[,\r\n\t<>]',word) or unsafe.search(word):continue
    if key in out:continue
    note=context_notes(sense,w.get('tags',[]),k.get('tags',[]))
    description=fixes['overrides'].get(seed['word'],seed['meaning'])
    meaning=description if not note or description.startswith(note) else note+description
    out[key]=dict(reading=reading,word=word,meaning=meaning,entryId=e['id'],senseNumber=1,contextNote=note,
      senseTags=sense['misc'],dialectTags=sense['dialect'],formTags=w.get('tags',[]),readingTags=k.get('tags',[]),
      seed=seed,gap='new-reading' if reading not in readings else 'alternate-spelling',
      sourceKana=k['text'],sourceWord=word,common=k['common'] or w.get('common',False),
      relation='identical-single-sense-gloss-set' if seed.get('equivalentGlossSet') else 'same-single-dictionary-noun-sense',reviewStatus='source-equivalent-editorial-origin')
    out[key]['meaningChecks']=[dict(synset=d['synset']) for d in checks]
    out[key]['trustedEditorialSeed']=seed['id'] in trusted
    out[key]['seedDefinitionCorrection']=dict(original=seed['meaning'],replacement=description) if description!=seed['meaning'] else None
    out[key]['meaningReviewScope']='individually-edited-seed' if seed['id'] in trusted else 'inherited-existing-description-single-source-sense'
 rows=sorted(out.values(),key=lambda x:(x['gap']!='new-reading',not x['common'],not x['seed']['editorial'],len(x['reading']),x['reading'],x['word']))
 (D/'alias-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 (D/'alias-meaning-holds.json').write_text(json.dumps(held,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(baselineSha256=hashlib.sha256(raw).hexdigest(),candidates=len(rows),newReadings=len({x['reading'] for x in rows}-readings),gaps=dict(collections.Counter(x['gap'] for x in rows)),counts=counts),ensure_ascii=False))
 for x in rows[:110]:print(x['word'],x['reading'],x['gap'],x['meaning'])
if __name__=='__main__':main()
