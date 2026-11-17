"""Apply one fixed researched batch, retaining existing IDs, assets and grades."""
import argparse, csv, hashlib, io, json
from pathlib import Path
from datetime import datetime, timezone
from shiritori_manifest import read_manifest, write_manifest

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('review',nargs='?',default='data/meaning-review/source-check-20261118-batch0001.json')
args=parser.parse_args()
REVIEW=Path(args.review).as_posix()
def dump(path,value):
    (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(data):return hashlib.sha256(data).hexdigest()
def append_history(original,records):
    newline='\r\n' if b'\r\n' in original else '\n'
    pieces=[]
    for record in records:
        item=dict(record);ids=item.pop('currentOriginalIds',None)
        text=json.dumps(item,ensure_ascii=False,indent=2)
        if ids is not None:text=text[:-2]+',\n  "currentOriginalIds": '+json.dumps(ids,separators=(',',':'))+'\n}'
        pieces.append('\n'.join('  '+line for line in text.splitlines()).replace('\n',newline))
    prefix=original.rstrip()[:-1].rstrip()
    return prefix+(','+newline+(','+newline).join(pieces)+newline+']'+newline).encode()
batch=json.loads((ROOT/REVIEW).read_text(encoding='utf-8'))
first_batch=REVIEW.endswith('-batch0001.json')
image_links_removed=set(batch.get('imageLinksRemoved',[354] if first_batch else []))
source=(ROOT/'whitelist.csv').read_bytes()
assert digest(source)==batch['baselineSha256'],'Apply only to the fixed reviewed baseline'
original_lines=source.decode('utf-8-sig').splitlines()
output_lines=original_lines.copy()
reader=csv.DictReader(io.StringIO(source.decode('utf-8-sig')))
headers=reader.fieldnames; rows=list(reader);before=[dict(r) for r in rows]
assert len(headers)==9 and len({r['id'] for r in batch['changes']})==len(batch['changes'])
if batch.get('rowRange'):
    first_row,last_row=batch['rowRange']
    assert all(first_row<=r['id']<=last_row for r in batch['changes'])
    assert set(range(first_row,last_row+1))=={r['id'] for r in batch['rowDecisions']}
assert image_links_removed<={r['id'] for r in batch['changes']}
grade=json.loads((ROOT/'data/shiritori-grade-decisions.json').read_text(encoding='utf-8'))
assert grade['sourceSha256']==digest(source) and grade['reviewedRows']==len(rows)
old_count=len(rows)
history_bytes=(ROOT/'data/dictionary-imports/history.json').read_bytes()
history=json.loads(history_bytes)
assert history[-1]['afterSha256']==digest(source)
serialize=lambda row:','.join(row.get(h,'') for h in headers)
changes=[]; remap={}
for r in batch['changes']:
    i=r['id']-1; prev=rows[i]
    assert (prev['reading'],prev['word'],prev['meaning'])==(r['beforeReading'],r['beforeWord'],r['beforeMeaning'])
    assert r['status']=='source-checked' and r['expressionReview']=='checked'
    assert str(i) in grade['levels'][str(r['effectiveLevel'])].split()
    if r['effectiveLevel']==1:assert r['level1Review']=='checked'
    after={**prev,**{k:r[k] for k in ('reading','word','meaning')}}
    if r['id'] in image_links_removed:after.update(image_asset='',image_mode='none',image_credit='')
    assert all(',' not in value and '\n' not in value for value in after.values())
    changes.append(dict(originalId=i+1,before=original_lines[i+1],after=serialize(after)))
    output_lines[i+1]=serialize(after)
    remap[(prev['reading'],prev['word'],prev['meaning'])]=(after['reading'],after['word'],after['meaning'])
    rows[i]=after
text='\n'.join(output_lines)+'\n'
history.append(dict(type='vocabulary-corrections',batch=REVIEW,beforeSha256=digest(source),afterSha256=digest(text.encode()),sourceRows=old_count,currentOriginalIds=list(range(1,old_count+1)),changes=changes))
after_corrections=digest(text.encode())
addition_csv=[]; addition_reviews=[]
for r in batch['additions']:
    assert r['status']=='source-checked' and r['expressionReview']==r['senseCoverageReview']=='checked'
    after=dict.fromkeys(headers,'');after.update(reading=r['reading'],word=r['word'],meaning=r['meaning'],level=str(min(r['effectiveLevel'],3)),image_mode='none')
    assert not any((x['reading'],x['word'],x['meaning'])==(after['reading'],after['word'],after['meaning']) for x in rows)
    grade['levels'][str(r['effectiveLevel'])]+=' '+str(len(rows))
    grade['notes'][str(len(rows))]='2026-11-18: 調査した独立語義。既存行から難易度を転用せず語義に応じて判断。'
    rows.append(after);addition_csv.append(serialize(after))
    addition_reviews.append(dict(reading=r['reading'],word=r['word'],meaning=r['meaning'],lexicalSource=r['sources'][0],meaningReason=r['evidence'],ageReason=grade['notes'][str(len(rows)-1)],distinctSenseReason=r['senseCoverageNote'],imageReason='新しい別義は説明のみ。既存画像を別義へ流用しない。'))
final_text=text+'\n'.join(addition_csv)+'\n'
add_path=batch.get('additionsCsv','data/dictionary-imports/2026-11-18-consistency500-senses.csv')
(ROOT/add_path).write_text(','.join(headers)+'\n'+'\n'.join(addition_csv)+'\n',encoding='utf-8')
dump(add_path.replace('.csv','.review.json'),addition_reviews)
history.append(dict(batch=add_path,beforeSha256=after_corrections,afterSha256=digest(final_text.encode()),addedLines=addition_csv))
grade.update(sourceSha256=digest(final_text.encode()),reviewedRows=len(rows),reviewDate='2026-11-18')

# Preserve every immutable prompt, crop record and image hash. Only current labels change.
manifest=read_manifest()
detached_assets={Path(before[i-1]['image_asset']).name for i in image_links_removed}
for asset in manifest['assets']:
    key=tuple(asset.get(k,'') for k in ('reading','word','meaning'))
    detached=asset.get('file') in detached_assets
    if detached:
        asset['aliases']=[a for a in asset.get('aliases',[]) if a.get('id') not in image_links_removed]
        asset['currentAssignmentNote']='2026-11-18: 修正後の語義と一致しない現行の割り当てを解除。生成時の記録は保持。'
    elif key in remap:asset.update(zip(('reading','word','meaning'),remap[key]))
    for alias in asset.get('aliases',[]):
        key=tuple(alias.get(k,'') for k in ('reading','word','meaning'))
        if key in remap:alias.update(zip(('reading','word','meaning'),remap[key]))
write_manifest(ROOT/'assets/shiritori/manifest.json',manifest)

# Existing image fingerprints were verified by earlier registrations. No image was edited.
catalog=json.loads((ROOT/'data/image-coverage/review-updates.json').read_text(encoding='utf-8'))
now=datetime.now(timezone.utc).isoformat(timespec='seconds')
previous_catalog_sha=catalog['csvSha256']
# The published baseline already had an older priority catalog (a strict CSV
# prefix). Extend that prefix without inventing dates or recomputing images.
assert len(catalog['entries'])<=old_count
for i,entry in enumerate(catalog['entries']):
    assert entry['text']==[before[i][k] for k in ('reading','word','meaning')]
    assert entry['image_asset']==before[i]['image_asset']
assert {r['image_asset'] for r in before if r['image_asset']}<=set(catalog['images'])
for i,r in enumerate(before[len(catalog['entries']):],len(catalog['entries'])+1):
    catalog['entries'].append(dict(id=i,text=[r[k] for k in ('reading','word','meaning')],textUpdatedAt='',image_asset=r['image_asset'],imageAssignedAt=''))
for r in batch['changes']:
    entry=catalog['entries'][r['id']-1]
    assert tuple(entry['text'])==(r['beforeReading'],r['beforeWord'],r['beforeMeaning'])
    entry['text']=[r['reading'],r['word'],r['meaning']];entry['textUpdatedAt']=now
    if r['id'] in image_links_removed:entry['image_asset']='';entry['imageAssignedAt']=''
for i,r in enumerate(rows[old_count:],old_count+1):
    catalog['entries'].append(dict(id=i,text=[r['reading'],r['word'],r['meaning']],textUpdatedAt=now,image_asset='',imageAssignedAt=''))
catalog['csvSha256']=digest(final_text.encode())
catalog['revision']=digest(json.dumps({k:v for k,v in catalog.items() if k!='revision'},ensure_ascii=False,sort_keys=True).encode())
(ROOT/'whitelist.csv').write_bytes(final_text.encode())
(ROOT/'data/dictionary-imports/history.json').write_bytes(append_history(history_bytes,history[-2:]))
dump('data/shiritori-grade-decisions.json',grade)
(ROOT/'data/image-coverage/review-updates.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
summary=dict(beforeSha256=digest(source),afterSha256=digest(final_text.encode()),sourceRows=old_count,currentRows=len(rows),corrected=len(changes),added=len(addition_csv),existingGradesPreserved=True,imageBinariesChanged=False,imageLinksRemoved=sorted(image_links_removed),previousPriorityCatalogSha256=previous_catalog_sha,priorityCatalogReconciledByExactPrefix=True)
dump(batch.get('applicationRecord','data/meaning-review/consistency500-application.json'),summary)
print(json.dumps(summary))
