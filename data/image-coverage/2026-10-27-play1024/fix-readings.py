import json,re,hashlib,csv
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;B=H/'2026-10-27-play1024'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
rows=read(B.with_suffix('.review.json'));plan=read(H/'manifest-additions.json')
fix={'百族の長 プチョヘンザ':'みあもじゃぷちょへんざ','勝熱英雄 モモキング':'じょーねつひーろーももきんぐ','龍素記号Xf クローチェ・フオーコ':'りゅうそきごうえっくすえふくろーちぇふおーこ','爆熱剣 バトライ刃':'ばくねつけんばとらいば','バトライ刃':'ばとらいば','爆熱DX バトライ武神':'ばくねつでらっくすばとらいぶしん','バトライ武神':'ばとらいぶしん','王来英雄 モモキングRX':'おーらいひーろーももきんぐれっくす','モモキングアールエックス':'ももきんぐれっくす','パーリ騎士':'ぱーりないっ','DNA・スパーク':'でぃえぬえーすぱーく'}
sources={x['word']:x for x in read(H/'dm-readings.json')}
replace={'エナジー・リバース':('クリスタル・メモリー','くりすたるめもりー','『デュエル・マスターズ』の山札から札を一枚選んで手札に加える呪文。'),'ポッポ・ジュヴィラ':('神滅翔天ポッポ・ジュヴィラ','しんめつしょうてんぽっぽじゅゔぃら','『デュエル・マスターズ』の墓地を使った進化を助けるクリーチャー。')}
for x in rows:
 if x['word'] in replace:
  w,r,m=replace[x['word']];x.update(word=w,reading=r,meaning=m,canonical=w,imagequery=w)
  fix[w]=r
 if x['word'] in fix:
  x['reading']=fix[x['word']]
  if x['word']=='モモキングアールエックス':x['word']='モモキングレックス'
 if x['canonical'] in sources:
  x['lexicalSource']['readingEvidence']=sources[x['canonical']]
  x['lexicalSource']['readingReview']='個別カード辞典のルビと照合。通常の漢字読みから推測しない。'
changed=read(H/'reading-corrections.json') if (H/'reading-corrections.json').exists() else []
cats=list(dict.fromkeys(x['category'] for x in rows));colors=['#175c74','#755029','#345c3a','#525095','#845142','#385c81','#6b4273','#6c5337','#326565','#734b68']
for entry in plan:
 replacement=entry['word'] in replace
 if replacement:
  w,r,m=replace[entry['word']];entry.update(word=w,meaning=m);fix[w]=r
 if entry['word'] not in fix or (entry['reading']==fix[entry['word']] and not replacement):continue
 oldfile=entry['file'];entry['file']=Path(oldfile).stem+'-v2.png';entry['reading']=fix[entry['word']]
 family=[x for x in rows if x['image_asset'].endswith('/'+oldfile)]
 for x in family:x['image_asset']='assets/shiritori/'+entry['file']
 for a in entry['aliases']:
  x=next(x for x in family if x['id']==a['id']);a.update(reading=x['reading'],word=x['word'],meaning=x['meaning'])
 accent=colors[cats.index(family[0]['category'])];im=Image.new('RGB',(256,256),'#fbfaf5');d=ImageDraw.Draw(im)
 d.rounded_rectangle((9,9,246,246),radius=18,fill='white',outline=accent,width=3);d.rounded_rectangle((18,18,237,48),radius=8,fill=accent)
 def centered(t,y,f,c):
  b=d.textbbox((0,0),t,font=f);d.text(((256-b[2]+b[0])/2,y-b[1]),t,font=f,fill=c)
 regular='C:/Windows/Fonts/BIZ-UDGothicR.ttc';bold='C:/Windows/Fonts/BIZ-UDGothicB.ttc'
 centered('デュエマのカード',27,ImageFont.truetype(regular,13),'white')
 def wrap(t,f):
  out=[];line=''
  for c in t:
   if line and d.textlength(line+c,font=f)>208:out.append(line);line=c
   else:line+=c
  if line:out.append(line)
  return out
 for size in range(27,12,-1):
  f=ImageFont.truetype(bold,size);lines=wrap(entry['word'],f)
  if len(lines)*(size+7)<=117:break
 top=65+(117-len(lines)*(size+7))/2
 for i,line in enumerate(lines):centered(line,top+i*(size+7),f,'#172d39')
 f=ImageFont.truetype(regular,12);lines=wrap(entry['reading'],f)
 if len(lines)>3:f=ImageFont.truetype(regular,10);lines=wrap(entry['reading'],f)
 assert len(lines)<=3
 for i,line in enumerate(lines):centered(line,188+i*15,f,'#42545d')
 p=H/'assets'/entry['file'];im.save(p,optimize=True);entry['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
 changed.append(dict(before=oldfile,after=entry['file'],word=entry['word'],reading=entry['reading']))
save(H/'reading-corrections.json',changed);save(H/'manifest-additions.json',plan);save(B.with_suffix('.review.json'),rows)
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
B.with_suffix('.csv').write_text(header+'\n'+'\n'.join(','.join(str(x[k]) for k in header.split(',')) for x in rows)+'\n',encoding='utf-8',newline='\n')
spec=read(H/'diagram-play1024-namecards.json');spec['renderer']='data/image-coverage/2026-10-27-play1024/build.py + fix-readings.py'
spec['cards']=[dict(file=x['file'],word=x['word'],reading=x['reading'],sha256=x['sha256']) for x in plan];save(H/'diagram-play1024-namecards.json',spec)
print(json.dumps(dict(correctedFiles=len(changed),correctedRows=sum(x['word'] in fix for x in rows)),ensure_ascii=False))
