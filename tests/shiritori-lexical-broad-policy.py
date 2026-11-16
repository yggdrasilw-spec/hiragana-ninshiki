"""Difficulty may not suppress a source-attested, content-appropriate term."""
import csv,json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
policy=json.loads((R/'data/lexical-expansion/adoption-policy.json').read_text(encoding='utf-8'))
assert policy['version']==2 and not policy['difficultyIsRejectionReason']
items=[]
for p in (R/'data/dictionary-imports').glob('2026-11-16-related-closure*.review.json'):
 items.extend(x for x in json.loads(p.read_text(encoding='utf-8')) if x.get('adoptionPolicyVersion')==2 and not x.get('withdrawn'))
assert items
advanced=[x for x in items if x['lexicalSource'].get('inheritedGrade',0)>=4]
historical=[x for x in items if set(x['lexicalSource'].get('senseTags',[])) & {'arch','obs','dated'}]
dialect=[x for x in items if x['lexicalSource'].get('dialectTags')]
assert advanced and historical and dialect
for x in items:
 assert x['grade']==4 and x['provisional']
 assert 'ok' not in x['lexicalSource'].get('readingTags',[]),'Historical spelling must not be treated as modern pronunciation'
 if x['lexicalSource'].get('contextNote'):assert x['meaning'].startswith(x['lexicalSource']['contextNote'])
 assert not any(bad in x['meaning'] for bad in ['ある人に対する個人的興味からくる計画','知性が通常より劣る','伊勢を扱う','旗艦などを扱う'])
 if x['word']=='白米':assert '精米した米' in x['meaning']
 if x['word'] in {'マージャン','麻雀'}:assert '144' not in x['meaning']
baseline=subprocess.check_output(['git','show','1b516476:whitelist.csv'],cwd=R)
raw=(R/'whitelist.csv').read_bytes();assert raw.startswith(baseline)
rejections=json.loads((R/'data/lexical-expansion/meaning-scope-rejections.json').read_text(encoding='utf-8'))
assert rejections['withdrawnBeforePublication']>=10
rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
report=dict(passed=True,policy2ActiveItems=len(items),advancedSeeds=len(advanced),historical=len(historical),dialect=len(dialect),publishedBaselinePreserved=True,
 sourceSha256=hashlib.sha256(raw).hexdigest(),currentRows=len(rows),currentReadings=len({x['reading'] for x in rows}))
print(json.dumps(report,ensure_ascii=False))
