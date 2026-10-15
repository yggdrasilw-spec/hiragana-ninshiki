"""Build labelled visual QA overviews without changing any source or crop."""
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c'
p=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));available=[];missing=[]
for n in range(1,p['sheets']+1):
 x=next(x for x in p['newImages'] if x['sheet']==n)
 if not (ROOT/x['cropValidation']).exists():missing.append(n);continue
 available.append((n,ROOT/'assets/shiritori'/x['sourceSheet']))
font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',27)
for start in range(0,len(available),4):
 overview=Image.new('RGB',(1280,1360),'white');d=ImageDraw.Draw(overview)
 for j,(n,path) in enumerate(available[start:start+4]):
  im=Image.open(path).convert('RGB');im.thumbnail((640,640));x=j%2*640;y=j//2*680
  d.text((x+15,y+5),f'Sheet {n:02} / {path.stem}',font=font,fill='#12364c');overview.paste(im,(x,y+40))
 overview.save(OUT/f'illustration-review-{start//4+1:02}.png')
reuse=p['reuseReviews'];im=Image.new('RGB',(1024,1024),'white');d=ImageDraw.Draw(im)
for j,x in enumerate(reuse):
 src=Image.open(ROOT/x['candidates'][0]['image_asset']).convert('RGB');src.thumbnail((300,280));cx=j%3*340;cy=j//3*340
 im.paste(src,(cx,cy+42));d.text((cx+10,cy+3),x['group'],font=font,fill='#12364c')
im.save(OUT/'reuse-review.png')
print(json.dumps(dict(available=[n for n,_ in available],missing=missing)))
