"""Freeze the sense-level plan and 16-cell prompts; resumable generation."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-16-expansion1024f';OUT=ROOT/'data/image-coverage'/NAME
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
items=json.loads((OUT/'candidates.json').read_text(encoding='utf-8'))
aliases={'セレス':'ケレス','ティタン':'タイタン','アルクトゥルス':'アークトゥルス','ベクルックス':'ミモザ','ボート競技':'ローイング','重量挙げ':'ウエイトリフティング','シンクロナイズドスイミング':'アーティスティックスイミング','唐傘小僧':'からかさお化け','ぬっぺふほふ':'ぬっぺっぽう','グリフィン':'グリフォン','不死鳥':'フェニックス','キュクロプス':'サイクロプス','ハルピュイア':'ハーピー','ドワルフ':'ドワーフ','吸血鬼':'ヴァンパイア','ウェアウルフ':'狼男','プレゼン':'プレゼンテーション','オーバーオール':'サロペット','ジャンプスーツ':'オールインワン','カッティングボード':'まな板','ホイッパー':'泡立て器','カラテ':'空手'}
byword={x['word']:x for x in items if x['imagePolicy']=='generate'}
draw=[]
for i,x in enumerate(items,1):
 x['slot']=i
 if x['imagePolicy']=='none':continue
 target=aliases.get(x['word'])
 if target in byword:x['reuseSlot']=byword[target].get('slot') or items.index(byword[target])+1
 else:draw.append(x)
for n in range((len(draw)+15)//16):
 group=draw[n*16:(n+1)*16];cells=[]
 for k,x in enumerate(group,1):x.update(sheet=n+1,tileIndex=k);cells.append(dict(slot=x['slot'],word=x['word'],meaning=x['meaning'],category=x['category']))
 while len(cells)<16:cells.append(dict(slot=None,word='unused botanical decoration',meaning='An unlabelled green leaf branch. Padding only; do not register.',category='padding'))
 prompt='''Use case: scientific-educational / illustration-story.
Edit the attached equal 4x4 template: keep the square 2048x2048 canvas, ALL five full vertical and five full horizontal straight continuous pure magenta #ff00ff lines including outer borders, same line thickness, and exactly equal cells. Paint only the sixteen white interiors, row-major order. Single clear educational illustration per cell, generous use of its own cell, no prescribed blank-margin ratio. No words, letters, digits, labels, logos, watermarks, commercial packages or modern copyrighted character designs. Magenta is reserved for the grid lines. Draw every object and shadow wholly inside its own cell. Use clean, warm, easily recognized children's encyclopedia art. Sports depict physically plausible equipment and safe representative poses, no emblems, no Olympic rings, no letters or numbers on clothing. Mythic beings: original designs based on traditional descriptions, friendly non-graphic depiction, clothed people; no imitation of any manga/game designs. Astronomy: explicitly conceptual scientific illustration rather than a photograph; isolated astronomical body on dark space within the cell. A star is a luminous stellar sphere, NOT a five-point cartoon and NOT a planet; use the described color, do not invent surface continents or claim exact texture. If the body's appearance is unknown, show only a simple neutral small body with a schematic orbit around its parent planet (not misleading invented detailed terrain). Planet and moon hues and rings must match established features. Different objects are not required to be on a shared size scale. Daily objects and abstract concepts use a concrete simple scene that demonstrates the definition.
The EXACT sixteen cells, left to right then top to bottom:\n'''
 for k,c in enumerate(cells,1):prompt+=f'{k}. [{c["category"]}] {c["word"]}: {c["meaning"]}\n'
 (OUT/f'sheet{n+1:02}.prompt.txt').write_text(prompt,encoding='utf-8')
 save(OUT/f'sheet{n+1:02}.cells.json',cells)
save(OUT/'plan.json',dict(name=NAME,items=items,newIllustrations=len(draw),reuse=len([x for x in items if 'reuseSlot' in x]),sheets=(len(draw)+15)//16,explanationOnly=len([x for x in items if x['imagePolicy']=='none'])))
print(json.dumps(dict(rows=len(items),draw=len(draw),sheets=(len(draw)+15)//16),ensure_ascii=False))
