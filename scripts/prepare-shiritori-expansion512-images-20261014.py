"""Prepare the current missing image IDs and exact 16-cell prompt order."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-14-expansion512-images'
OUT=ROOT/'data/image-coverage'/NAME
OUT.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
selected=json.loads((ROOT/'data/dictionary-imports/2026-10-14-expansion512.review.json').read_text(encoding='utf-8'))
items=[]
for x in selected:
    matches=[(i,r) for i,r in enumerate(rows,1) if all(r[k]==x[k] for k in ('reading','word','meaning'))]
    assert len(matches)==1
    i,r=matches[0]
    if r['image_asset']:continue
    items.append(dict(id=i,reading=r['reading'],word=r['word'],meaning=r['meaning'],level=int(r['level']),
        filename=f'expansion512-oct14-word-{i}.png',scene=r['word']+'：'+r['meaning']))
assert len(items)==512
base='''Edit the attached exact 2048x2048 equal-size 4 by 4 template. Paint EXACTLY sixteen separate vocabulary illustrations in its white cells, row-major left to right then top to bottom. Preserve ALL FIVE horizontal and FIVE vertical straight continuous pure MAGENTA #ff00ff lines including the outer frame, their exact positions and 8px thickness. Do not move, erase, cover, bend or resize the grid. Magenta ONLY for grid lines, never artwork. Use each cell generously, no large blank margins. All subjects and scenes remain entirely within their own cells and never cross the grid. No captions, labels, letters, numbers, readable text, watermarks or extra panels. Clear warm watercolor children's picture-book illustrations with correct anatomy. Give each word its own specific concrete example matching ONLY its given meaning. For verbs show an unambiguous action (small motion arrows if useful); for abstract qualities show a plausible situation, not an unexplained symbol. If before/after is necessary, contain the pair inside the one assigned cell. Do not merge neighbouring concepts. Backgrounds should be visually simple so subjects remain clear at 256px. Convey changes and relationships visually without written words. Here are the sixteen meanings in exact cell order:\n'''
for n in range(32):
    group=items[n*16:(n+1)*16]
    for t,x in enumerate(group,1):x.update(sheet=n+1,tileIndex=t,sourceSheet=f'sheets/expansion512-oct14-sheet{n+1:02}.png',cropValidation=f'data/image-coverage/{NAME}/sheet{n+1:02}-crop.json')
    prompt=base+'\n'.join(f'{i}. {x["scene"]}' for i,x in enumerate(group,1))
    (OUT/f'sheet{n+1:02}-prompt.txt').write_text(prompt,encoding='utf-8')
    for x in group:x['prompt']=prompt
plan=dict(date='2026-10-14',baselineRows=len(rows),baselineSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),
    template='C:/Users/user/.codex/skills/shiritori-image-sheets/assets/equal-grid-4x4.png',count=len(items),items=items)
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'missing':len(items),'sheets':32}))
