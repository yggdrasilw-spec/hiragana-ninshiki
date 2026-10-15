"""Reproducible, sense-specific diagrams for screen operations and game concepts."""
import csv,hashlib,json,math,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c'
P=OUT/'plan.json';plan=json.loads(P.read_text(encoding='utf-8'))
BLUE='#24628b';INK='#233c50';GREEN='#2d9a78';RED='#dc6643';PALE='#e8f3f6';GOLD='#edb544'
FONT='C:/Windows/Fonts/meiryo.ttc'
def text(d,xy,s,size=37,color=INK,width=660):
 f=ImageFont.truetype(FONT,size)
 while d.textbbox((0,0),s,font=f)[2]>width and size>15:
  size-=1;f=ImageFont.truetype(FONT,size)
 d.text(xy,s,font=f,fill=color,anchor='mm')
def rr(d,box,fill=PALE,outline=BLUE,w=5,r=18):d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)
def arrow(d,a,b,color=RED,w=9):
 d.line([a,b],fill=color,width=w);t=math.atan2(b[1]-a[1],b[0]-a[0]);d.polygon([b,(b[0]-27*math.cos(t-.5),b[1]-27*math.sin(t-.5)),(b[0]-27*math.cos(t+.5),b[1]-27*math.sin(t+.5))],fill=color)
def person(d,x,y,color=BLUE,scale=1,wave=False):
 s=scale;d.ellipse((x-30*s,y-80*s,x+30*s,y-20*s),fill='#f4cda8',outline=INK,width=3)
 rr(d,(x-45*s,y-15*s,x+45*s,y+100*s),color,INK,3,18)
 d.line([(x-20*s,y+100*s),(x-30*s,y+165*s)],fill=INK,width=max(2,int(12*s)));d.line([(x+20*s,y+100*s),(x+35*s,y+165*s)],fill=INK,width=max(2,int(12*s)))
 d.line([(x-45*s,y+10*s),(x-75*s,y+(60 if not wave else -50)*s)],fill=INK,width=max(2,int(10*s)));d.line([(x+45*s,y+10*s),(x+75*s,y+60*s)],fill=INK,width=max(2,int(10*s)))
def monitor(d,dark=False):
 rr(d,(85,190,683,570),'#263544' if dark else 'white',INK,8,25)
 d.rectangle((330,573,438,614),fill=INK);rr(d,(248,611,520,629),INK,INK,2,5)
def cloud(d,x,y):
 for a,b,r in [(x-60,y,48),(x,y-25,60),(x+60,y,48)]:d.ellipse((a-r,b-r,a+r,b+r),fill=PALE,outline=BLUE,width=5)
 d.rectangle((x-80,y,x+80,y+45),fill=PALE)
def doc(d,box,label='あ'):
 rr(d,box,'white',BLUE,5,9);x1,y1,x2,y2=box;text(d,((x1+x2)//2,(y1+y2)//2),label,52,width=x2-x1-20)
def screen_lines(d,left,right,dark=False):
 monitor(d,dark);text(d,(384,290),left,46,'white' if dark else BLUE,width=540);text(d,(384,420),right,42,'white' if dark else INK,width=540)
recipes={}
for l in (OUT/'diagram-recipes.txt').read_text(encoding='utf-8').splitlines():
 if l and not l.startswith('#'):
  g,kind,a,b,caption=l.split('|');recipes[g]=(kind,a,b,caption)
brand_recipes={
 'YouTube':('video','YouTube','どうがを みる','どうがの サービス'),
 'Roblox':('blocks','つくる','あそぶ','いろいろな ゲームの せかい'),
 'Minecraft':('voxel','つくる','ぼうけん','ブロックの せかい'),
 'Splatoon':('ink','ぬる','チームで しょうぶ','インクを ぬって たたかう'),
 'MarioKart':('race','マリオカート','GOAL','カートで レース'),
 'AnimalCrossing':('island','くらす','しまを つくる','しまの くらしを たのしむ'),
 'SmashBros':('platform','たたかう','ふっとばす','キャラクターで たいせん'),
 'Switch2':('console','Nintendo Switch 2','','ゲームきの しくみの 図'),
 'Switch':('console','Nintendo Switch','','ゲームきの しくみの 図'),
 'GameChat':('friends','ゲームを する','こえで はなす','あそびながら はなす'),
 'GameShare':('network','ソフトが ある','ソフトが ない','たいおうソフトを わけて あそぶ'),
 'MarioKartWorld':('race','つながる コース','GOAL','ひろい せかいで レース'),
 'Bananza':('rocks','こわす','すすむ','ちけいを こわして ぼうけん'),
 'Pokopia':('island','メタモン','まちづくり','ポケモンたちと くらす まちへ'),
 'AirRiders':('race','マシンで はしる','そらも とぶ','マシンで かける レース'),
 'TennisFever':('tennis','ラケット','テニス','いろいろな ラケットで しょうぶ'),
 'Creative':('voxel','ざいりょうを えらぶ','じゆうに つくる','マインクラフトの あそびかた'),
 'Survival':('voxel','ざいりょうを あつめる','いきのこる','マインクラフトの あそびかた')}
def build(x):
 group=x['group'];kind,a,b,caption=brand_recipes[group[6:]] if group.startswith('brand:') else recipes[group]
 im=Image.new('RGB',(768,768),'#fffdf7');d=ImageDraw.Draw(im)
 rr(d,(18,18,750,750),'#fffdf7','#d9e6ea',4,32)
 text(d,(384,87),x['word'],49,width=690)
 if kind in ('screen','dark','browser','study','slide'):
  screen_lines(d,a,b,kind=='dark')
  if kind=='browser':rr(d,(110,207,657,245),'#e2edf1',BLUE,2,8);text(d,(384,226),'https://example.invalid',22)
  if kind=='slide':d.ellipse((130,340,220,430),fill=GOLD);d.line((260,370,580,370),fill=BLUE,width=10)
 elif kind in ('flow','cable','download','upload','network'):
  rr(d,(56,242,338,500),'white',BLUE);rr(d,(430,242,712,500),'white',GREEN)
  if kind=='cable':d.line([(337,380),(430,380)],fill=INK,width=14);d.rectangle((370,360,405,400),fill=INK)
  else:arrow(d,(340,370),(425,370))
  text(d,(197,350),a,32,width=260);text(d,(571,350),b,32,width=260)
  for cx,col in [(197,BLUE),(571,GREEN)]:d.ellipse((cx-30,430,cx+30,490),fill=col)
 elif kind in ('letters','symbol','key'):
  if kind=='key':rr(d,(180,250,588,480),'#eaf1f4',INK,7,32)
  text(d,(384,345),a,112 if kind=='symbol' and len(a)<5 else 70)
  if b:text(d,(384,480 if kind!='key' else 430),b,60)
 elif kind=='bar':
  text(d,(384,245),a,75)
  if '/' in b:
   num,den=map(int,b.split('/'));ratio=num/den
   rr(d,(110,345,658,420),'white',BLUE,7,15);rr(d,(120,355,120+528*ratio,410),GREEN,GREEN,1,10);text(d,(384,505),b,66)
  elif '→' in b:
   before,after=map(int,b.split('→'))
   for j,(value,col) in enumerate([(before,BLUE),(after,GREEN)]):rr(d,(150,340+j*95,150+460*value/after,400+j*95),col,col,1,9)
   text(d,(384,555),b,56)
  else:
   text(d,(384,360),b,100)
   for j in range(int(b)):d.ellipse((265+j*85,470,315+j*85,520),fill=GREEN)
 elif kind in ('copy','paste','cut'):
  doc(d,(75,250,290,510),'あ' if kind!='cut' else '');doc(d,(480,250,695,510),'あ');arrow(d,(310,380),(460,380));text(d,(185,550),'もと',35);text(d,(580,550),'うつす さき',35)
 elif kind=='gesture':
  rr(d,(130,180,638,580),'white',INK,7,25)
  if a.startswith('pinch'):
   inward=a=='pinchin';pairs=[((220,475),(320,375)),((550,270),(450,370))]
   d.rectangle((325,310,445,430) if inward else (280,265,490,475),outline=GREEN,width=6)
   for start,end in pairs:
    d.ellipse((start[0]-22,start[1]-22,start[0]+22,start[1]+22),fill=GOLD,outline=INK,width=3);arrow(d,start,end if inward else (start[0]+(start[0]-end[0])*.65,start[1]+(start[1]-end[1])*.65))
  elif a in ('swipe','scroll','drag','drop'):
   for j in range(4):rr(d,(185,235+j*65,435,270+j*65),PALE,BLUE,2,5)
   d.ellipse((285,455,335,505),fill=GOLD,outline=INK,width=3);arrow(d,(310,450),(510,300) if a in ('drag','drop') else (310,260))
   if a=='drop':rr(d,(485,255,575,345),'white',GREEN,5,5);text(d,(540,405),'はなす',27)
  else:
   rr(d,(255,275,510,430),PALE,BLUE,5);d.ellipse((340,330,390,380),fill=GOLD);text(d,(384,500),'1 → 2',55)
 elif kind=='mouse':
  rr(d,(245,225,523,555),'#eaf1f4',INK,7,95);d.line((384,230,384,390),fill=INK,width=5);d.line((250,390,518,390),fill=INK,width=5)
  d.ellipse((410 if a=='右' else 290,280,478 if a=='右' else 358,348),fill=GOLD);text(d,(384,615),a,44)
 elif kind in ('mute','volume','music'):
  d.polygon([(170,335),(250,335),(335,260),(335,505),(250,430),(170,430)],fill=BLUE)
  for r in [70,120,170]:d.arc((300-r,380-r,300+r,380+r),-60,60,fill=GREEN,width=10)
  if kind=='mute':d.line((130,245,510,535),fill=RED,width=17)
  elif kind=='volume':rr(d,(115,570,650,590),'#c9d8df',BLUE,2,5);d.ellipse((430,550,490,610),fill=GOLD)
  else:text(d,(535,360),'♪',125)
 elif kind in ('lock','airplane','notify'):
  monitor(d)
  if kind=='lock':
   d.arc((310,245,460,405),180,360,fill=BLUE,width=17);rr(d,(285,315,485,450),GOLD,BLUE,6);text(d,(384,505),a,50)
  elif kind=='airplane':
   d.polygon([(384,245),(414,350),(570,430),(560,460),(410,405),(410,485),(455,520),(450,540),(384,515),(318,540),(313,520),(358,485),(358,405),(208,460),(198,430),(354,350)],fill=BLUE)
  else:d.ellipse((297,245,470,415),fill=GOLD,outline=BLUE,width=7);text(d,(384,330),'!',100);text(d,(384,485),a,36)
 elif kind in ('apps','wallpaper','paint'):
  monitor(d);d.rectangle((100,205,668,550),fill='#c5e9f2');d.polygon([(100,550),(250,365),(390,550),(520,330),(668,550)],fill='#78b59a');d.ellipse((530,235,610,315),fill=GOLD)
  if kind=='apps':
   for j,s in enumerate(['♪','あ','＋','○','☆','□']):
    cx=215+j%3*170;cy=290+j//3*145;rr(d,(cx-50,cy-50,cx+50,cy+50),['white','#fff1cb','#b3e0d5'][j%3],BLUE,4,17);text(d,(cx,cy),s,54)
   if a=='highlight':d.ellipse((145,220,285,360),outline=RED,width=9)
  if kind=='paint':d.line((180,485,275,365,430,445,540,320),fill=RED,width=16);d.line((565,510,615,360),fill=INK,width=12)
 elif kind in ('friends','avatar'):
  rr(d,(50,195,345,580),'white',BLUE);rr(d,(423,195,718,580),'white',GREEN);person(d,198,340,BLUE,.8);person(d,571,340,GREEN,.8,group=='エモート');arrow(d,(347,330),(419,330));text(d,(198,540),a,27,width=278);text(d,(571,540),b,27,width=278)
 elif kind in ('chat','stamp'):
  monitor(d);rr(d,(135,240,520,345),'#d4ece8',GREEN,4,35);text(d,(327,292),a,43,width=360)
  if kind=='chat':rr(d,(255,390,635,495),PALE,BLUE,4,35);text(d,(445,443),b,40,width=350)
  else:person(d,390,440,GREEN,.55,True)
 elif kind=='mail':
  rr(d,(140,260,628,500),'white',BLUE,8,12);d.line((145,270,384,430,623,270),fill=BLUE,width=8);text(d,(384,575),a,39)
 elif kind=='site':
  doc(d,(240,195,530,325),a);d.line((384,328,384,385),fill=BLUE,width=7);d.line((205,385,565,385),fill=BLUE,width=7);d.line((205,385,205,425),fill=BLUE,width=7);d.line((565,385,565,425),fill=BLUE,width=7);doc(d,(85,425,325,555),'ページ A');doc(d,(445,425,685,555),'ページ B')
 elif kind=='folder':
  rr(d,(150,240,360,330),GOLD,BLUE,5,15);rr(d,(150,290,620,520),'#f3ca61',BLUE,6,15);text(d,(384,408),a,66)
 elif kind=='search':
  monitor(d);rr(d,(135,270,633,370),'white',BLUE,5,12);text(d,(365,320),a,37,width=400);d.ellipse((547,292,585,330),outline=BLUE,width=6);d.line((579,326,602,350),fill=BLUE,width=7)
  for j in range(3):d.line((150,420+j*45,560,420+j*45),fill='#b2c7d2',width=10)
 elif kind in ('keyboard','flick','handwrite'):
  if kind=='handwrite':monitor(d);text(d,(384,345),a,145);d.line((505,490,580,290),fill=INK,width=19)
  elif kind=='flick':
   for cx,cy,s in [(384,350,'あ'),(245,350,'い'),(384,215,'う'),(523,350,'え'),(384,485,'お')]:rr(d,(cx-60,cy-60,cx+60,cy+60),'white',BLUE,4,12);text(d,(cx,cy),s,70)
   arrow(d,(405,370),(520,400));d.ellipse((370,360,415,405),fill=GOLD)
  else:
   for j in range(30):
    cx=125+j%10*57;cy=330+j//10*70;rr(d,(cx-25,cy-25,cx+25,cy+25),'#c4e5d7' if group=='ホームポジション' and j//10==1 and j%10 in range(1,9) else 'white',BLUE,3,5)
   text(d,(384,240),a,50);rr(d,(230,520,538,565),'white',BLUE,4,6)
 elif kind in ('blocks','robot'):
  for j,s in enumerate([a,b,'くりかえす']):rr(d,(150,230+j*105,620,320+j*105),[PALE,'#c9e7d8','#f6ddb1'][j],BLUE,5,15);text(d,(384,275+j*105),s,42)
 elif kind in ('cube','voxel'):
  for cx,cy in ([(384,360)] if kind=='cube' else [(245,400),(384,400),(523,400),(384,280)]):
   d.polygon([(cx,cy-80),(cx+80,cy-40),(cx,cy),(cx-80,cy-40)],fill='#83c594',outline=INK,width=4);d.polygon([(cx-80,cy-40),(cx,cy),(cx,cy+90),(cx-80,cy+45)],fill='#ad845a',outline=INK,width=4);d.polygon([(cx,cy),(cx+80,cy-40),(cx+80,cy+45),(cx,cy+90)],fill='#896141',outline=INK,width=4)
  if kind=='voxel':text(d,(384,570),a+' → '+b,33)
 elif kind=='pixels':
  pattern=['01100110','11111111','11111111','01111110','00111100','00011000'] if a=='heart' else ['00000000','00000000','00010000','00000000','00000000','00000000']
  for yy,row in enumerate(pattern):
   for xx,c in enumerate(row):d.rectangle((180+xx*52,225+yy*52,232+xx*52,277+yy*52),fill=RED if c=='1' else '#e8eff1',outline='white',width=3)
 elif kind=='pictogram':person(d,384,300,BLUE,1.3);d.line((130,585,640,585),fill=BLUE,width=8)
 elif kind=='map':
  d.line((150,230,150,540,550,540,550,260),fill='#b9cbd1',width=45);rr(d,(290,210,460,360),'#bce0c9',GREEN,4,5);text(d,(375,280),'こうえん',42);d.ellipse((100,205,200,305),fill=RED);text(d,(150,255),'今',50,'white')
 elif kind=='qr':
  import qrcode
  qr=qrcode.QRCode(box_size=12,border=4);qr.add_data(a);qr.make(fit=True);tile=qr.make_image(fill_color=INK,back_color='white').convert('RGB');tile.thumbnail((410,410));im.paste(tile,((768-tile.width)//2,190));text(d,(384,620),'よみとると SHIRITORI',30)
 elif kind=='disc':
  d.ellipse((170,200,600,630),fill='#d1e7ed',outline=BLUE,width=8);d.ellipse((220,250,550,580),outline='#72b7c4',width=22);d.ellipse((345,375,425,455),fill='#fffdf7',outline=BLUE,width=7);text(d,(384,290),a,50)
 elif kind in ('video','loop','rhythm'):
  monitor(d);d.polygon([(330,280),(330,440),(470,360)],fill=GREEN);rr(d,(135,495,620,510),PALE,BLUE,2,4);d.ellipse((280,480,320,520),fill=GOLD)
  if kind=='loop':d.arc((210,215,555,490),20,330,fill=RED,width=9);arrow(d,(510,265),(550,300))
  else:text(d,(384,235),a,39);text(d,(384,455),b,36)
 elif kind in ('game','boss','items','shield','race','puzzle','ink','island','platform','console','rocks','tennis'):
  monitor(d)
  if kind=='shield':d.polygon([(270,260),(384,230),(500,260),(480,420),(384,490),(290,420)],fill='#b5d9ef',outline=BLUE,width=9);arrow(d,(150,300),(260,360))
  elif kind=='console':rr(d,(155,260,610,485),'#253c48',INK,7,20);rr(d,(225,280,540,465),'#bedcdd',BLUE,3,7);d.ellipse((173,292,207,326),fill=INK);d.ellipse((553,332,585,364),fill=INK);text(d,(384,535),a,32)
  elif kind=='puzzle':
   for j,s in enumerate(['1','2','3','4','5','6','7','8','']):cx=285+j%3*98;cy=265+j//3*98;rr(d,(cx-42,cy-42,cx+42,cy+42),PALE if s else 'white',BLUE,3,8);text(d,(cx,cy),s,46)
  elif kind=='ink':
   for j,(cx,cy,col) in enumerate([(200,300,BLUE),(490,360,GREEN),(350,480,BLUE)]):
    for n in range(8):t=n*math.pi/4;d.ellipse((cx-45+45*math.cos(t),cy-45+45*math.sin(t),cx+45+45*math.cos(t),cy+45+45*math.sin(t)),fill=col)
  elif kind=='island':d.ellipse((130,250,630,520),fill='#86c9de');d.ellipse((225,300,550,480),fill='#8bc78b');rr(d,(330,320,445,420),'#f2d39a',INK,3,4);d.polygon([(315,325),(388,260),(462,325)],fill=RED)
  elif kind=='rocks':
   for cx,cy in [(230,330),(360,420),(520,280)]:d.polygon([(cx-60,cy+30),(cx-50,cy-50),(cx+25,cy-65),(cx+75,cy),(cx+20,cy+65)],fill='#b5a592',outline=INK,width=4)
   arrow(d,(220,500),(570,350))
  elif kind=='tennis':
   d.rectangle((150,250,620,510),fill='#83c6a0',outline='white',width=7);d.line((385,250,385,510),fill='white',width=6);d.line((145,380,625,380),fill=INK,width=7);d.ellipse((260,290,292,322),fill=GOLD)
  elif kind=='race':
   d.line((150,510,300,240,470,240,620,510),fill='#c1d0d7',width=60);rr(d,(220,370,310,440),BLUE,INK,4,10);rr(d,(470,410,560,480),GREEN,INK,4,10);text(d,(384,280),'GOAL',40)
  elif kind=='items':
   d.ellipse((200,300,280,380),outline=GOLD,width=16);d.line((270,365,360,460),fill=GOLD,width=18);d.polygon([(520,275),(585,360),(520,445),(455,360)],fill=GREEN,outline=BLUE,width=6)
  else:
   d.line((130,500,630,500),fill=GREEN,width=18);person(d,240,335,BLUE,.6);person(d,535,310,RED,1 if kind=='boss' else .6);arrow(d,(315,395),(435,340))
  if (a or b) and kind!='console':text(d,(384,530),(a+'  '+b).strip(),32,width=540)
 else:raise ValueError((group,kind))
 text(d,(384,694),caption,34,width=685)
 source=ROOT/'assets/shiritori/sheets'/f'expansion512c-diagram-word-{x["id"]}.png'
 source.parent.mkdir(parents=True,exist_ok=True);im.save(source)
 target=ROOT/'assets/shiritori'/x['filename'];im.resize((256,256),Image.Resampling.LANCZOS).save(target)
 x.update(sourceSheet='sheets/'+source.name,tileIndex=1,generatedAt='2026-10-15',scene=caption,prompt=f'Program drawing recipe: {kind} / {a} / {b} / {caption}',sha256=hashlib.sha256(target.read_bytes()).hexdigest(),diagramKind=kind)
 return im
rendered=[]
for x in plan['diagrams']:rendered.append((x,build(x)))
for start in range(0,len(rendered),16):
 sheet=Image.new('RGB',(1024,1024),'white')
 for j,(_,im) in enumerate(rendered[start:start+16]):sheet.paste(im.resize((256,256),Image.Resampling.LANCZOS),((j%4)*256,(j//4)*256))
 sheet.save(OUT/f'diagram-review-{start//16+1:02}.png')
P.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(diagrams=len(rendered),reviewSheets=(len(rendered)+15)//16)))
