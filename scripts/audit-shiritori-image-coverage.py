"""Validate the complete word-level action/concept image coverage review."""
import argparse,csv,json,re
from pathlib import Path
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent.parent)
args=parser.parse_args();root=args.root.resolve()
with (root/'whitelist.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
report=json.loads((root/'data/image-coverage/review-2026-10-10.json').read_text(encoding='utf-8'))
manifest=json.loads((root/'assets/shiritori/manifest.json').read_text(encoding='utf-8'))
assert len(rows)==len(report),'Vocabulary changed: refresh the coverage review.'
assets={a['file']:a for a in manifest['assets']}
assert len(assets)==len(manifest['assets']),'Duplicate manifest asset names.'
targets=0;broken=[];missing=[];stale=[];referenced=set()
for i,(row,entry) in enumerate(zip(rows,report),1):
    assert entry['id']==i
    if any(row[k]!=entry[k] for k in ['reading','word','meaning','level','image_asset']):stale.append(i)
    asset=row['image_asset']
    if entry['target']:
        targets+=1
        if not asset:missing.append({'id':i,'word':row['word']})
        assert entry['category'] and entry['scopeReason']
    if asset:
        assert re.fullmatch(r'assets/shiritori/[A-Za-z0-9_-]+\.(png|jpe?g|webp)',asset,re.I)
        path=root/asset
        if not path.is_file():broken.append(asset);continue
        assert path.name in assets,'Asset absent from the provenance manifest: '+asset
        referenced.add(path.name)
        assert row['image_mode']=='asset' or row['image_mode']=='fallback'
for file,entry in assets.items():
    assert file in referenced,'Orphan manifest image: '+file
    assert entry['status']=='reviewed' and entry['prompt'] and entry['review']
    with Image.open(root/'assets/shiritori'/file) as im:
        im.verify()
    if entry.get('generatedAt')=='2026-10-10':
        with Image.open(root/'assets/shiritori'/file) as im:assert im.size==(256,256),file
assert not stale,f'Coverage metadata needs re-review at rows: {stale[:20]}'
assert not missing,f'Missing action/concept assets: {missing[:20]}'
assert not broken,f'Broken asset references: {broken[:20]}'
print(json.dumps({'passed':True,'vocabularyRows':len(rows),'reviewedTargetRows':targets,'assets':len(assets),'missingTargetAssets':len(missing),'brokenAssetReferences':len(broken)},ensure_ascii=False))
