"""Bind archived taxonomy pages and local lexical evidence to the reviewed plan."""
import json,re,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
p=json.loads((O/'plan.json').read_text(encoding='utf-8'));research=json.loads((O/'research.json').read_text(encoding='utf-8'));byname={r['label']:r for r in research}
cache=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json');lookup=collections.defaultdict(list)
def hira(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s).replace('・','').replace('＝','')
if cache.exists():
 for e in json.loads(cache.read_text(encoding='utf-8'))['words']:
  for kana in e.get('kana',[]):lookup[hira(kana['text'])].append(e['id'])
bound=0;jmdict=0
for x in p['items']:
 key=x.get('scientificName','') if x['category']=='reptiles' else x['category']
 if key in byname and byname[key]['status']=='retrieved':
  r=byname[key];x['lexicalSource'].update(archivedSource=r['path'],sourceSha256=r['sha256']);bound+=1
 ids=lookup.get(x['reading'],[])
 if ids:x['lexicalSource']['jmdictEntryIds']=ids;x['lexicalSource']['jmdictVersion']='jmdict-eng-3.6.2';jmdict+=1
 if x['reading']=='めたとろん':x['lexicalSource'].update(url='https://www.sefaria.org/Sanhedrin.38b?lang=bi',textReference='Babylonian Talmud Sanhedrin 38b')
 if x['category']=='frogs':x['lexicalSource']['taxonPresentInArchivedList']=x['scientificName'] in (R/byname['frogs']['path']).read_text(encoding='utf-8');assert x['lexicalSource']['taxonPresentInArchivedList']
for s in p['sheets']:s['tiles']=[x for x in p['items'] if x['sheet']==s['sheet']]
(O/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=dict(archivedReferences=bound,jmdictMatched=jmdict,reviewedMeanings=len(p['items']),researchRetrieved=sum(r['status']=='retrieved' for r in research),researchFailed=[r['label'] for r in research if r['status']!='retrieved'])
(O/'lexical-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(report))
