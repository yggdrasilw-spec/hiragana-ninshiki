"""Validate ten measured sheets and draw neutral name cards for protected subjects."""
import csv,hashlib,json,subprocess,sys,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-15-expansion512d';OUT=ROOT/'data/image-coverage'/NAME
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=read(OUT/'plan.json')
prior=read(ROOT/'data/image-coverage/2026-10-15-expansion512c/plan.json')
expected=prior['baselineRows']+len(prior['items'])
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
if any(r['reading']==p['items'][0]['reading'] for r in live):raise ValueError('Already imported: use validation tests rather than regenerating')
baseline=max(len(live),expected)
p.update(baselineRows=baseline,precedingBatch=prior['name'] if 'name' in prior else '2026-10-15-expansion512c')
for n,x in enumerate(p['items']):
 x.update(id=baseline+n+1,filename=f'expansion512d-{"card-" if n>=160 else ""}word-{baseline+n+1}.png')
save(OUT/'plan.json',p)
failed=[]
for n in range(1,11):
 group=[x for x in p['items'] if x.get('sheet')==n]
 source=ROOT/'assets/shiritori'/group[0]['sourceSheet']
 names=','.join(x['filename'][:-4] for x in group)
 cmd=[sys.executable,'-X','utf8','scripts/crop-shiritori-grid.py',str(source),'--names',names,'--output','assets/shiritori','--report',str(OUT/f'sheet{n:02}-crop.json')]
 if (OUT/f'sheet{n:02}-crop.json').exists():cmd.append('--verify-existing')
 if subprocess.run(cmd,cwd=ROOT).returncode:failed.append(n)
FONT='C:/Windows/Fonts/BIZ-UDGothicR.ttc'
def label(d,value,top,max_height,start_size=52):
 for size in range(start_size,25,-1):
  f=ImageFont.truetype(FONT,size);lines=[];line=''
  for c in value:
   if d.textbbox((0,0),line+c,font=f)[2]>650:lines.append(line);line=''
   line+=c
  if line:lines.append(line)
  gap=size+13
  if gap*len(lines)<=max_height:break
 assert gap*len(lines)<=max_height,(value,lines)
 for i,line in enumerate(lines):d.text((384,top+i*gap),line,anchor='mt',font=f,fill='#eff9ff' if start_size==52 else '#9bedd0')
 return dict(lines=lines,size=size)
layouts=[]
for x in p['items'][160:]:
 im=Image.new('RGB',(768,768),'#101c2b');d=ImageDraw.Draw(im)
 d.rounded_rectangle((26,26,742,742),24,outline='#72bca4',width=4)
 kind='スポーツ選手' if x['category'].startswith('選手:') else 'スポーツチーム' if 'チーム' in x['category'] else 'ゲーム名' if x['category']=='ゲーム' else 'キャラクター名'
 d.text((384,68),kind,anchor='mt',font=ImageFont.truetype(FONT,32),fill='#b6c7d3')
 title=label(d,x['word'],175,235);reading=label(d,x['reading'],470,190,38)
 d.text((384,694),'なまえを よんでみよう',anchor='mt',font=ImageFont.truetype(FONT,26),fill='#b6c7d3')
 source=ROOT/'assets/shiritori/sheets'/f'expansion512d-diagram-word-{x["id"]}.png'
 dest=ROOT/'assets/shiritori'/x['filename']
 # Reproducible code-native typography, with no borrowed visual identity.
 if source.exists():
  with Image.open(source) as old:changed=old.tobytes()!=im.tobytes()
  if changed:
   source=source.with_name(f'expansion512d-diagram-v2-word-{x["id"]}.png')
   x['filename']=f'expansion512d-card-v2-word-{x["id"]}.png';dest=ROOT/'assets/shiritori'/x['filename']
   if not source.exists():im.save(source)
   else:
    with Image.open(source) as old:assert old.tobytes()==im.tobytes()
 else:im.save(source)
 small=im.resize((256,256),Image.Resampling.LANCZOS)
 if dest.exists():
  with Image.open(dest) as old:assert old.tobytes()==small.tobytes()
 else:small.save(dest)
 x.update(sourceSheet=str(source.relative_to(ROOT/'assets/shiritori')).replace('\\','/'),tileIndex=1,scene='名称と読みのみの独自文字カード。肖像・ロゴ・キャラクターの姿は使用しない。')
 layouts.append(dict(id=x['id'],word=x['word'],title=title,reading=reading,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
save(OUT/'card-layouts.json',layouts)
save(OUT/'plan.json',p)
print(json.dumps(dict(staged=not failed,baselineRows=baseline,illustrations=160,cards=len(layouts),failedSheets=failed)))
if failed:sys.exit(1)
