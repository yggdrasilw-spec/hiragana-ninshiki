import json,csv,hashlib,importlib.util
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];META=ROOT/'data/integrations/english-stage-20261101'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=read(META/'plan.json');catalog=read(META/'asset-catalog.json');rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')))
assert len(rows)==plan['baselineRows']+len(plan['additions']);assert len(catalog)==len(plan['items'])
assert len({x['cardId'] for x in catalog})==len(catalog)
for a in catalog:
 p=ROOT/'assets/shiritori'/a['file'];assert sha(p)==a['sha256'];r=rows[a['vocabulary']['id']-1]
 assert (r['reading'],r['word'],r['meaning'])==tuple(a['vocabulary'][k] for k in ['reading','word','meaning'])
 assert r['image_asset'],'Dictionary meaning has no primary image'
 if a['dictionaryPrimary']:assert r['image_asset']=='assets/shiritori/'+a['file']
 with Image.open(p) as im:assert im.size==(256,256)
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for n in range(1,4):grid.verify_report(META/f'sheet{n:02}-crop.json',ROOT/'assets/shiritori/sheets'/f'eiken-20261101-sheet{n:02}.png',ROOT/'assets/shiritori')
validation=read(META/'diagram-validation.json');assert validation['rendererSha256']==hashlib.sha256((META/'render-diagrams.py').read_text(encoding='utf-8').encode('utf-8')).hexdigest()
for d in validation['diagrams']:
 assert sha(ROOT/'assets/shiritori'/d['file'])==d['sha256'];assert sha(ROOT/'assets/shiritori'/d['sourceSheet'])==d['sourceSha256']
 if d['type']=='number':assert d['semantics']['quantity']==d['semantics']['dotCount']
 if d['type']=='clock':assert 1<=d['semantics']['hour']<=12 and d['semantics']['minute']==0
 if d['type']=='month':assert d['semantics']['calendarMonths']==12 and 1<=d['semantics']['highlightMonth']<=12
 for used in d['reusedIllustrations']:assert sha(ROOT/'assets/shiritori'/used['file'])==used['sha256']
print(json.dumps(dict(passed=True,cards=len(catalog),newVocabulary=len(plan['additions']),rasterSheets=3,croppedImages=48,diagrams=len(validation['diagrams']))))
