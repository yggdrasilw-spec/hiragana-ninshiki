"""Walk source cross-references to closure and retain each discovery's parent."""
import collections,csv,hashlib,json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion'
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
def main():
 jm=json.loads((R/'data/general10000/sources/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
 entries={e['id']:e for e in jm['words']};forms=collections.defaultdict(set);safe={}
 inappropriate=re.compile(r'性玩具|陰茎|膣|性交|自慰|売春|猥褻|麻薬|覚醒剤|\b(?:sex|sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide)\b',re.I)
 for e in jm['words']:
  senses=[(i,s) for i,s in enumerate(e['sense'],1) if set(s['partOfSpeech']) & {'n','n-t','n-adv','n-vs'} and not s['dialect'] and not set(s['misc']) & {'arch','obs','rare','vulg','derog','sl','dated','sens','X'} and not inappropriate.search(' '.join(g['text'] for g in s['gloss']))]
  if not senses:continue
  safe[e['id']]=senses
  for f in e['kanji']+e['kana']:
   forms[norm(f['text'])].add(e['id'])
 links=collections.defaultdict(set)
 unresolved=0
 for eid,senses in safe.items():
  for number,s in senses:
   for relation in ['related','antonym']:
    for ref in s[relation]:
     if not ref or not isinstance(ref[0],str):continue
     targets=forms.get(norm(ref[0]),set())
     if len(ref)>1 and isinstance(ref[1],str):targets={t for t in targets if any(hira(k['text'])==hira(ref[1]) for k in entries[t]['kana'])}
     if not targets:unresolved+=1
     for target in targets:
      if target==eid:continue
      links[eid].add((target,relation,number));links[target].add((eid,'referenced-by-'+relation,number))
 seeds={}
 for file in sorted((R/'data/dictionary-imports').glob('2026-11-16-related-closure*.review.json')):
  for x in json.loads(file.read_text(encoding='utf-8')):
   eid=x.get('lexicalSource',{}).get('entryId')
   if eid in safe:seeds[eid]='registered-related-vocabulary'
 for file in ['queue.jsonl','alias-candidates.jsonl','wordnet-candidates.jsonl']:
  if not (D/file).exists():continue
  for line in (D/file).read_text(encoding='utf-8').splitlines():
   x=json.loads(line)
   for e in x.get('evidence',[]):
    if e['entryId'] in safe:seeds.setdefault(e['entryId'],file)
   if x.get('entryId') in safe:seeds.setdefault(x['entryId'],file)
 seenfile=D/'related-seen.json'
 seen=json.loads(seenfile.read_text(encoding='utf-8')) if seenfile.exists() else {}
 seen={eid:record for eid,record in seen.items() if eid in safe}
 for eid,origin in seeds.items():seen.setdefault(eid,dict(depth=0,parentEntryId=None,relation='seed',origin=origin))
 frontier=collections.deque(sorted(seen));rounds=collections.Counter();processed=0
 while frontier:
  eid=frontier.popleft();processed+=1;rounds[seen[eid]['depth']]+=1
  for target,relation,number in sorted(links[eid]):
   if target in seen:continue
   seen[target]=dict(depth=seen[eid]['depth']+1,parentEntryId=eid,relation=relation,parentSenseNumber=number)
   frontier.append(target)
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()));pairs={(r['reading'],norm(r['word'])) for r in old}
 blocked=[]
 for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);blocked.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
 candidates={};counts=collections.Counter()
 for eid,path in sorted(seen.items(),key=lambda z:(z[1]['depth'],z[0])):
  e=entries[eid]
  for k in e['kana']:
   reading=hira(k['text'])
   if any(reading==v if mode=='exact' else v in reading for mode,v in blocked):continue
   if not re.fullmatch('[ぁ-ゖー]{1,30}',reading) or reading.startswith('ん'):continue
   if set(k['tags']) & {'ik','ok','rk','gikun'}:continue
   for w in e['kanji'] or [dict(text=k['text'],tags=[])]:
    word=w['text'];key=(reading,norm(word))
    if set(w['tags']) & {'iK','ik','oK','rk'}:continue
    if '*' not in k['appliesToKanji'] and word not in k['appliesToKanji']:continue
    if re.search(r'[\s,\r\n\t()（）/／]',word) or inappropriate.search(word):continue
    applicable=[i for i,s in safe[eid] if ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) and ('*' in s['appliesToKanji'] or word in s['appliesToKanji'])]
    if not applicable or key in candidates:continue
    present=key in pairs
    candidates[key]=dict(reading=reading,word=word,entryId=eid,applicableSenseNumbers=applicable,discovery=path,
      status='surface-present-senses-unchecked' if present else 'pending-source-and-meaning-review',
      url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&seq='+eid)
    counts['presentPairs' if present else 'missingPairs']+=1
    if not present and path['depth']>0:counts['newlyLinkedMissingPairs']+=1
 (D/'related-queue.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in candidates.values()),encoding='utf-8')
 seenfile.write_text(json.dumps(seen,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 result=dict(schema=1,baselineSha256=hashlib.sha256(raw).hexdigest(),seedEntries=len(seeds),visitedEntries=len(seen),processedEntries=processed,
  rounds=dict(sorted(rounds.items())),frontier=[],reachableGraphExhausted=True,unresolvedReferences=unresolved,pairs=len(candidates),counts=counts,
  limits=['A completed walk is coverage of reachable source references, not completeness of Japanese.','Graph discovery never grants adoption or confirms child suitability.'])
 (D/'related-checkpoint.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
