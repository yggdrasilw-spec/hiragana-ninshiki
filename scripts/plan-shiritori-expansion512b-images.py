import csv,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-14-expansion512b'
OUT=ROOT/'data/image-coverage'/NAME
plan=json.loads((OUT/'authored-plan.json').read_text(encoding='utf-8'))
old=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))[:plan['baselineRows']]
byreading={}
for i,r in enumerate(old,1):
 if r['image_asset']:byreading.setdefault(r['reading'],[]).append(dict(id=i,**r))
reuse={}
for line in (OUT/'reuse-editorial.txt').read_text(encoding='utf-8').splitlines():
 a,b=line.split('|');reuse[a]=b
items=plan['items'];bynew={x['reading']:x for x in items}
REJECTED={'うかべる':'人が水に浮く場面では、物を水面へ置く動作がわからない。',
 'うごかす':'自分が走る場面では、物を動かす動作を示せない。',
 'うごきだす':'走っている絵だけでは、停止状態からの開始がわからない。',
 'かいちゅう':'海面の風景で、水中の場面ではない。',
 'かざかみ':'風向計だけでは風上の相対的な位置がわからない。',
 'せんさい':'微細な粒の絵では、細かな作りを示せない。',
 'たちあがる':'共有候補は挙手の場面で、座位からの変化がない。',
 'つもる':'共有候補の「つもり」は意図の意味で、積雪とは違う。',
 'とりだす':'手渡す場面で、容器の中から出すことがわからない。',
 'ながれこむ':'滝の風景だけでは流入先を明確に示せない。'}
(OUT/'rejected-reuse.json').write_text(json.dumps(REJECTED,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
unavailable=[]
for x in items:
 if x['reading'] in REJECTED:x['group']=x['reading'];continue
 group=x['group']
 rd=reuse.get(x['reading'],group[1:] if group.startswith('@') else None)
 if not rd:continue
 if rd not in byreading:
  unavailable.append([x['reading'],rd]);x['group']=x['reading'];continue
 matches=byreading[rd]
 # Explicit sense disambiguation for the only shared homonym used here.
 if rd=='いたむ':matches=[r for r in matches if r['word']=='傷む']
 r=matches[0]
 x.update(sourceId=r['id'],filename=Path(r['image_asset']).name,credit=r['image_credit'],
  reuseReason='共有元「'+r['word']+'」の場面を、この説明の具体例として使う。'+x['meaning'],
  sourceMeaning=r['meaning'],sourceWord=r['word'],sourceReading=r['reading'],assignment='reused')
groups={}
def key(x,seen=None):
 seen=set() if seen is None else seen
 assert x['reading'] not in seen,x['reading']
 seen.add(x['reading'])
 if x.get('sourceId'):return '@'+x['filename']
 g=x['group']
 if g!=x['reading'] and g in bynew:return key(bynew[g],seen)
 return x['reading']
for x in items:
 g=key(x)
 if g.startswith('@'):
  if not x.get('sourceId'):
   src=next(z for z in items if '@'+z.get('filename','')==g and z.get('sourceId'))
   for k in ('sourceId','filename','credit','sourceMeaning','sourceWord','sourceReading'):x[k]=src[k]
   x.update(assignment='reused',reuseReason='同じ対象の場面を共有。'+x['meaning'])
  continue
 groups.setdefault(g,[]).append(x)
new=[]
for g,members in groups.items():
 primary=next(x for x in members if x['reading']==g)
 new.append(dict(id=primary['id'],reading=primary['reading'],word=primary['word'],meaning=primary['meaning'],
  filename=f'expansion512b-word-{primary["id"]}.png',sharedIds=[x['id'] for x in members],members=members,
  scene=' / '.join(x['word']+'：'+x['meaning'] for x in members)))
base='''Edit this exact 2048x2048 4 by 4 grid template. Paint EXACTLY 16 independent educational vocabulary illustrations, left-to-right, top-to-bottom. KEEP the five vertical and five horizontal continuous PURE MAGENTA #ff00ff grid lines including the entire outer border, in their exact positions and thickness. Do not cover or move the lines. Magenta is reserved for the grid. No captions, letters, written text, numbers, labels, speech text, logos or watermarks. Clear warm children's picture-book watercolor with simple backgrounds, correct human anatomy, large legible subjects. All artwork remains entirely inside its own cell. Use cell space generously. For actions make who does what unambiguous, using small motion arrows or a before/after pair WITHIN the same cell when useful. For abstract qualities show a specific understandable example. A slash separates words sharing that SAME depicted action, not separate illustrations; show the common concrete scene for all meanings. Each cell must have a different picture. Exact row-major subjects:\n'''
sheet_count=math.ceil(len(new)/16)
for i,x in enumerate(new):
 n=i//16+1;t=i%16+1
 x.update(sheet=n,tileIndex=t,sourceSheet=f'sheets/expansion512b-sheet{n:02}.png',cropValidation=f'data/image-coverage/{NAME}/sheet{n:02}-crop.json')
 for member in x['members']:
  member.update(filename=x['filename'],credit='AI生成イラスト',assignment='new' if member['id']==x['id'] else 'shared-new',
   sourceId=x['id'],reuseReason='同じ場面の動作・結果を共有。'+member['meaning'])
for n in range(1,sheet_count+1):
 group=[x for x in new if x['sheet']==n]
 # Filler copies remain in the source sheet but are never added to the dictionary.
 scenes=[x['scene'] for x in group]
 scenes+=['A simple distinct school object: '+w for w in ['wooden pencil','blue eraser','green ruler','yellow notebook','red school bag','open sketchbook','paint brush','white chalk','pair of scissors','glue stick','folded origami crane','small bell','bookmark','pencil case','globe','clock'][:16-len(scenes)]]
 prompt=base+'\n'.join(f'{i+1}. {scene}' for i,scene in enumerate(scenes))
 (OUT/f'sheet{n:02}-prompt.txt').write_text(prompt,encoding='utf-8')
 for x in group:x['prompt']=prompt
plan.update(items=items,newImages=new,sheets=sheet_count,template='C:/Users/user/.codex/skills/shiritori-image-sheets/assets/equal-grid-4x4.png')
(OUT/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(words=len(items),existingReuse=sum(x['assignment']=='reused' for x in items),newImages=len(new),sheets=sheet_count,unavailable=unavailable),ensure_ascii=False))
