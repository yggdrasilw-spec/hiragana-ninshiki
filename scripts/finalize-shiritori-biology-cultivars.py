import csv,hashlib,json,subprocess,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-17-biology-generated'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
p=read(O/'plan.json');before=(R/'whitelist.csv').read_bytes()
with (R/'whitelist.csv').open(encoding='utf-8',newline='') as f:
 reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
assert len(rows)==12894
staged=[];batches=[];seen=set()
for sheet in p['sheets']:
 n=sheet['sheet'];v=O/f'sheet{n:02}-v2-staged.json';v=v if v.exists() else O/f'sheet{n:02}-staged.json'
 s=read(v);assert s['mechanicalPassed'] and s['semanticPassed'],v
 assert s['semanticSheetSha256']==sha((R/'assets/shiritori'/s['sourceSheet']).read_bytes())
 assert s['approvedIds']==[x['id'] for x in s['tiles'] if not x.get('filler')]
 staged.append(s)
 for x in s['tiles']:
  if x.get('filler'):continue
  i=x['id'];assert i not in seen;seen.add(i);r=rows[i-1]
  assert r['reading']==x['reading'] and r['word']==x['word']
  assert not r['image_asset'],(i,r['word'])
  batches.append(dict(id=i,reading=r['reading'],word=r['word'],meaning=r['meaning'],filename=x['filename'],scene=r['word']+'：'+r['meaning'],sourceSheet=s['sourceSheet'],tileIndex=x['tileIndex'],generatedAt='2026-10-17',prompt=s['prompt'],cropValidation=s['cropValidation'],credit='AI生成イラスト'))
assert len(batches)==p['uniqueImages']==578
batch=O/'images.csv';assert not batch.exists()
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(batches[0]),lineterminator='\n');w.writeheader();w.writerows(batches)
subprocess.run([sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(batch)],cwd=R,check=True)
before_alias=(R/'whitelist.csv').read_bytes()
with (R/'whitelist.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
m=read(R/'assets/shiritori/manifest.json');assets={x['file']:x for x in m['assets']};aliases=[]
for x in p['items']:
 r=rows[x['id']-1]
 if r['image_asset']:continue
 assert x.get('aliasOfReading'),x['word']
 candidates=[(i,a) for i,a in enumerate(rows,1) if a['reading']==x['aliasOfReading'] and a['meaning']==r['meaning']]
 assert len(candidates)==1,(x['word'],candidates)
 parentid,parent=candidates[0];assert parent['image_asset']
 for k in ['image_asset','image_mode','image_credit']:r[k]=parent[k]
 asset=assets[Path(r['image_asset']).name];assert not any(a['id']==x['id'] for a in asset['aliases'])
 asset['aliases'].append(dict(id=x['id'],originalId=None,reading=r['reading'],word=r['word'],meaning=r['meaning'],reuseReason='同じ対象を指す別の読み。語義を照合して生成画像を共有。',sourceReview='元の語と語義・対象が同じことを確認。',sourceId=parentid))
 aliases.append(dict(id=x['id'],sourceId=parentid,image_asset=r['image_asset']))
assert len(aliases)==12,len(aliases)
with (R/'whitelist.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
after=(R/'whitelist.csv').read_bytes();save(R/'assets/shiritori/manifest.json',m)
hpath=R/'data/dictionary-imports/history.json';h=read(hpath);assert h[-1]['afterSha256']==sha(before_alias)
h.append(dict(type='image-assets',batches=['data/image-coverage/2026-10-17-biology-generated/shared-aliases.json'],beforeSha256=sha(before_alias),afterSha256=sha(after),modifiedLines=[dict(id=i,before=b,after=a) for i,(b,a) in enumerate(zip(before_alias.decode().splitlines()[1:],after.decode().splitlines()[1:]),1) if b!=a]));save(hpath,h);save(O/'shared-aliases.json',aliases)
for name in ['2026-10-17-biology-cultivars','2026-10-17-snakes-danger']:
 path=R/f'data/dictionary-imports/{name}.review.json';items=read(path)
 for x in items:
  r=rows[x['id']-1]
  for k in ['meaning','image_asset','image_mode','image_credit']:x[k]=r[k]
  x['ageReason']=x['ageReason'].replace('制限なしの学習帯','「はってん」レベル')
  x['imageReason']='語義と特徴を照合した生成イラストを保存。同じ意味の別読みは画像を共有。品種同定用の写真ではない。'
 save(path,items)
 summary=read(R/f'data/dictionary-imports/{name}.summary.json');summary.update(imageAfterSha256=sha(after),generatedImages=sum(x['id'] in seen for x in items),sharedSavedImages=sum(x['id'] not in seen for x in items),wikimediaSearchWords=0);save(R/f'data/dictionary-imports/{name}.summary.json',summary)
for x in p['items']:
 r=rows[x['id']-1]
 for k in ['meaning','image_asset','image_mode','image_credit']:x[k]=r[k]
 x['ageReason']=x['ageReason'].replace('制限なしの学習帯','「はってん」レベル')
for s in p['sheets']:
 for x in s['tiles']:
  if not x.get('filler'):
   for k in ['meaning','image_asset','image_mode','image_credit']:x[k]=rows[x['id']-1][k]
coverage=read(R/'data/image-coverage/review-2026-10-10.json')
for x in coverage:
 if x['id']<=12300:continue
 r=rows[x['id']-1];assert r['image_asset']
 x.update(meaning=r['meaning'],image_asset=r['image_asset'],status='reviewed',assignment='new' if x['id'] in seen else 'reused')
save(R/'data/image-coverage/review-2026-10-10.json',coverage)
d=read(R/'data/shiritori-grade-decisions.json');d['sourceSha256']=sha(after);save(R/'data/shiritori-grade-decisions.json',d)
subprocess.run([sys.executable,'-X','utf8','scripts/build-shiritori-grade-bands.py'],cwd=R,check=True)
subprocess.run([sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py'],cwd=R,check=True)
stats=dict(addedWords=594,generatedImages=578,sharedImages=16,approvedSheets=37,totalRows=len(rows),beforeSha256=sha(before),afterSha256=sha(after),aliases=aliases)
p['registered']=stats;save(O/'plan.json',p);save(O/'summary.json',stats);print(json.dumps(stats,ensure_ascii=False))
