"""Render deterministic authored name cards and resolve shared vocabulary assets.

These are typography, not generated character illustrations. Canonical entries
and abbreviations share one file and one exact explanation.
"""
import csv,json,hashlib,collections,shutil,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;ROOT=Path('C:/Users/user/hiragana-ninshiki')
BASE=HERE/'2026-10-27-play1024';OUT=HERE/'assets';OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
rows=read(BASE.with_suffix('.review.json'));parents=read(BASE.with_suffix('.existing-canonicals.json'))
old=list(csv.DictReader((ROOT/'whitelist.csv').read_text(encoding='utf-8').splitlines()))
parentmap={x['id']:x for x in parents};groups=collections.defaultdict(list)
for x in rows:groups[x['canonical']].append(x)
fontpath='C:/Windows/Fonts/BIZ-UDGothicB.ttc'
regular='C:/Windows/Fonts/BIZ-UDGothicR.ttc'
colors=['#175c74','#755029','#345c3a','#525095','#845142','#385c81','#6b4273','#6c5337','#326565','#734b68']
cats=list(dict.fromkeys(x['category'] for x in rows));manifest=read(ROOT/'assets/shiritori/manifest.json')
byfile={x['file']:x for x in manifest['assets']};plan=[];existing=[]
for canonical,aliases in groups.items():
 first=next((x for x in aliases if x['word']==canonical),aliases[0]);parent=parentmap.get(first.get('existingCanonicalId'))
 if parent:
  allaliases=[dict(parent,category=first['category'])]+aliases;display=parent['word'];reading=parent['reading'];ident=parent['id']
 else:
  allaliases=aliases;display=canonical;reading=first['reading'];ident=first['id']
 # Different labels of exactly the same hero share the canonical description.
 descriptions={x['meaning'] for x in allaliases};assert len(descriptions)==1,(canonical,descriptions)
 if parent and parent['image_asset']:
  file=Path(parent['image_asset']).name;credit=parent['image_credit'];assert file in byfile
  existing.append(dict(file=file,aliases=aliases,canonicalId=ident))
 else:
  file=f'play1024-name-word-{ident}.png';credit='独自文字カード（外部検索なし）'
  accent=colors[cats.index(first['category'])];im=Image.new('RGB',(256,256),'#fbfaf5');d=ImageDraw.Draw(im)
  d.rounded_rectangle((9,9,246,246),radius=18,fill='white',outline=accent,width=3)
  d.rounded_rectangle((18,18,237,48),radius=8,fill=accent)
  label=first['category'].replace('トレーディングカードのタイトル','カードゲーム').replace('トランプ・カード遊び','トランプと遊び').replace('ボード・市販カードゲーム','ボード・カードゲーム').replace('デュエル・マスターズのカード','デュエマのカード')
  label=label.replace('日常の遊び','みんなの遊び')
  def centered(text,y,font,fill):
   box=d.textbbox((0,0),text,font=font);d.text(((256-(box[2]-box[0]))/2,y-box[1]),text,font=font,fill=fill)
  centered(label,27,ImageFont.truetype(regular,13),'white')
  def wrap(text,font,width):
   out=[];line=''
   for c in text:
    if line and d.textlength(line+c,font=font)>width:out.append(line);line=c
    else:line+=c
   if line:out.append(line)
   return out
  for size in range(27,12,-1):
   f=ImageFont.truetype(fontpath,size);lines=wrap(display,f,208)
   if len(lines)*(size+7)<=117:break
  assert size>=13 and len(lines)*(size+7)<=117,(display,lines)
  top=65+(117-len(lines)*(size+7))/2
  for i,line in enumerate(lines):centered(line,top+i*(size+7),f,'#172d39')
  rf=ImageFont.truetype(regular,12);rl=wrap(reading,rf,208)
  if len(rl)>3:
   rf=ImageFont.truetype(regular,10);rl=wrap(reading,rf,208)
  assert len(rl)<=3,(display,rl)
  for i,line in enumerate(rl):centered(line,188+i*15,rf,'#42545d')
  im.save(OUT/file,optimize=True)
  entry=dict(reading=reading,word=display,meaning=first['meaning'],file=file,mode='asset',credit=credit,prompt='独自組版の名称カード。白地の枠内にカテゴリ・正式名・ひらがなの読みだけを配置。作品の画像・公式ロゴ・カード面は使わない。',review='名称・読み・説明の対応と文字枠内の収まりをプログラム照合。代表カードを目視点検。',status='reviewed',generatedAt='2026-10-28',sourceSheet='sheets/diagram-play1024-namecards.json',tileIndex=1,renderer='Pillow ImageDraw / BIZ UDGothic typography',sha256=sha((OUT/file).read_bytes()),aliases=[])
  for x in allaliases:
   entry['aliases'].append(dict(id=x['id'],originalId=None,reading=x['reading'],word=x['word'],meaning=x['meaning'],reuseReason='同じ作品・人物・遊び・カードの正式名と略称。説明と画像を完全共有。' if x.get('aliasOf') else 'この名称の専用文字カード。',sourceReview='canonical='+canonical))
  plan.append(entry)
 for x in aliases:
  x.update(image_asset='assets/shiritori/'+file,image_mode='asset',image_credit=credit,imageReason='正式名「'+canonical+'」と同じ対象を指す名称カードまたは登録済み画像を共有。異なる作品やカードの絵を流用しない。')
 for x in parents:
  if x['id']==ident:x.update(image_asset='assets/shiritori/'+file,image_mode='asset',image_credit=credit)
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
BASE.with_suffix('.csv').write_text(header+'\n'+'\n'.join(','.join(str(x[k]) for k in header.split(',')) for x in rows)+'\n',encoding='utf-8',newline='\n')
save(BASE.with_suffix('.review.json'),rows);save(BASE.with_suffix('.existing-canonicals.json'),parents)
save(HERE/'manifest-additions.json',plan);save(HERE/'manifest-reused.json',existing)
spec=dict(kind='authored-typographic-cards',generatedAt='2026-10-28',renderer='scripts/build-shiritori-play1024-cards.py',size=[256,256],font=fontpath,notes='文字組版のためImageGenの4×4イラスト・切り出し工程の対象外。イラスト生成や既存画像の編集を行わない。',cards=[dict(file=x['file'],word=x['word'],reading=x['reading'],sha256=x['sha256']) for x in plan])
save(HERE/'diagram-play1024-namecards.json',spec)
summary=read(BASE.with_suffix('.summary.json'));summary.update(newImages=len(plan),reusedExistingImages=len(existing),sharedAliasRows=sum('aliasOf' in x for x in rows),existingCanonicalImages=len(parents))
save(BASE.with_suffix('.summary.json'),summary)
for name in ['preview.png']:
 samples=[plan[i] for i in [0,20,70,120,180,260,350,450,550,650,750,len(plan)-1] if i<len(plan)]
 preview=Image.new('RGB',(256*4,256*3),'white')
 for i,x in enumerate(samples):preview.paste(Image.open(OUT/x['file']),(i%4*256,i//4*256))
 preview.save(HERE/name)
print(json.dumps(summary,ensure_ascii=False))
