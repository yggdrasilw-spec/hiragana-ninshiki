"""Plan ten equal-grid sheets for 152 music words, plus eight unused fill cells."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-15-expansion512e'
p=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
music=[x for x in p['items'] if x['category'] in ['楽器','音楽ジャンル']]
scenes=[s for s in (OUT/'music-scenes.txt').read_text(encoding='utf-8').splitlines() if s and not s.startswith('#')]
assert len(music)==len(scenes)==152,(len(music),len(scenes))
items=[]
for i,(x,scene) in enumerate(zip(music,scenes)):
 items.append(dict(slot=x['slot'],reading=x['reading'],word=x['word'],meaning=x['meaning'],category=x['category'],scene=scene,sheet=i//16+1,tileIndex=i%16+1,sourceSheet=f'sheets/expansion512e-music-sheet{i//16+1:02}.png',filler=False))
for i in range(8):
 items.append(dict(slot=None,word='未登録の補助コマ',scene=scenes[i],sheet=10,tileIndex=i+9,sourceSheet='sheets/expansion512e-music-sheet10.png',filler=True))
base="""Use case: scientific-educational / illustration-story.
EDIT TARGET: the attached exact equal 4 by 4 white-cell template. Paint sixteen distinct vocabulary illustrations, in exact row-major order.
Preserve the 2048x2048 canvas and ALL FIVE vertical and ALL FIVE horizontal continuous straight pure MAGENTA #ff00ff divider lines, INCLUDING THE OUTER FRAME, with their original positions and widths. Do not erase, bend, move, cover or resize the lines. Magenta is ONLY for lines; no magenta in the paintings.
Each illustration is completely contained in its own cell; no objects or shadows cross into another cell. Use each cell generously, no mandatory large blank margins. Exactly 16 cells, no additional panels.
Clear warm watercolor and fine ink children's educational picture-book illustrations. Accurate functional musical instrument construction and normal human anatomy. All performers are wholly original anonymous adults, modestly dressed, no famous faces, franchise characters, copyrighted album covers, logos, branding, printed sheet-music, letters, numbers, labels, captions or watermarks. The music styles are illustrative examples of performance, never claim a genre has one fixed costume or ethnicity. No alcohol, drugs, weapons or aggressive symbols. Keep backgrounds simple and subject shapes readable at 256px.
The following SIXTEEN DIFFERENT scenes are in exact cell order. The numbered list is instructions ONLY; never draw the numbers:
"""
for n in range(1,11):
 group=[x for x in items if x['sheet']==n]
 prompt=base+'\n'.join(f'{x["tileIndex"]}. {x["scene"]}' for x in group)+'\n'
 (OUT/f'music-sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8')
 (ROOT/'assets/shiritori/sheets'/f'expansion512e-music-sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8')
(OUT/'music-plan.json').write_text(json.dumps(dict(words=152,sheets=10,fillerCells=8,items=items),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(words=152,sheets=10,fillerCells=8)))
