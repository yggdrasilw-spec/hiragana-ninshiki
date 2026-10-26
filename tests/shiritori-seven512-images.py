"""Cross-file acceptance checks for exactly512 existing senses receiving pictures."""
import collections,csv,hashlib,json
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
if not (R/'whitelist.csv').exists():R=Path('C:/Users/user/hiragana-ninshiki')
O=R/'data/image-coverage/2026-10-25-seven512-images'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda x:hashlib.sha256(x).hexdigest()
p=read(O/'plan.json');items=p['items'];reviews=read(O/'semantic-review.json');baseline=read(O/'baseline-state.json')
assert len(items)==len({x['id'] for x in items})==512
assert dict(collections.Counter(x['category'] for x in items))==p['categoryCounts']
assert len(reviews)==32 and {x['sheet'] for x in reviews}==set(range(1,33))
before=list(csv.DictReader((O/'registration-baseline.csv').open(encoding='utf-8-sig')));current=list(csv.DictReader((R/'whitelist.csv').open(encoding='utf-8-sig')))
assert len(before)==len(current)==16574
index={x['id']:x for x in items};later=read(R/'data/image-coverage/2026-10-25-seven512b-images/plan.json')['items'];later_ids={x['id'] for x in later};assert len(later_ids)==512 and not later_ids&set(index);changed=[]
for ident,(old,new) in enumerate(zip(before,current),1):
 if old!=new:changed.append(ident)
 for k in old:
  if ident not in set(index)|later_ids or k not in ['image_asset','image_mode','image_credit']:assert old[k]==new[k],(ident,k)
 if ident in index:
  x=index[ident];assert new['image_asset']=='assets/shiritori/'+x['filename'];assert new['image_mode']=='asset' and new['image_credit']=='AI生成イラスト'
assert set(changed)==set(index)|later_ids
manifest=read(R/'assets/shiritori/manifest.json');assets=manifest['assets'];assert len(assets)==baseline['manifestAssets']+1024
assert sha(json.dumps(assets[:baseline['manifestAssets']],ensure_ascii=False,sort_keys=True).encode())==baseline['manifestPrefixSha256']
byfile={x['file']:x for x in assets};assert len(byfile)==len(assets)
coverage=read(R/'data/image-coverage/review-2026-10-10.json');grades=read(R/'data/shiritori-grade-review.json');decisions=read(R/'data/shiritori-grade-decisions.json')
assert sha(json.dumps(decisions['levels'],sort_keys=True).encode())==baseline['gradeLevelsSha256']
for review in reviews:
 group=[x for x in items if x['sheet']==review['sheet']];assert review['approvedSlots']==[x['slot'] for x in group]
 stage=read(O/f"sheet{review['sheet']:02}-{review['version']}-staged.json")
 report=read(R/stage['cropValidation']);assert report['passed']
 assert sha((R/'assets/shiritori'/review['sourceSheet']).read_bytes())==report['sourceSha256']==review['sourceSha256']
 assert {x['file'] for x in report['tiles']}=={x['filename'] for x in group}
 for tile in report['tiles']:
  file=R/'assets/shiritori'/tile['file'];assert sha(file.read_bytes())==tile['sha256']
  with Image.open(file) as image:assert image.size==(256,256)
for x in items:
 a=byfile[x['filename']];aliases=[y for y in a['aliases'] if y['id']==x['id']];assert len(aliases)==1
 for k in ['reading','word','meaning']:assert aliases[0][k]==x[k]
 assert sha((R/'assets/shiritori'/x['filename']).read_bytes())==a['sha256']
 assert coverage[x['id']-1]['status']=='covered' and coverage[x['id']-1]['image_asset']==x['image_asset']
 assert grades[x['id']-1]['level']==x['grade']
hist=read(R/'data/dictionary-imports/history.json');assert hist[-1]['type']=='image-assets' and len(hist[-1]['modifiedLines'])==512 and hist[-1]['afterSha256']==sha((R/'whitelist.csv').read_bytes())
delivery=read(O/'r2-validation.json');assert delivery['complete'] and delivery['publicDownloadedAndSha256Matched']==512
print(json.dumps(dict(passed=True,assignedImages=512,unchangedVocabularyRows=16574,sourceSheets=32,sourceAndTileHashesMatched=True,unchangedEarlierAssets=baseline['manifestAssets'],gradeLevelsPreserved=True,publicSha256Matched=512)))
