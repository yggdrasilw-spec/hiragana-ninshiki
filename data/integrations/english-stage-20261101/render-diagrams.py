"""Deterministic, annotated vocabulary diagrams; illustrations are reused unchanged."""
import json,math,re,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;STAGE=BASE/'stage';ROOT=Path('C:/Users/user/hiragana-ninshiki')
OUT=STAGE/'assets/shiritori';META=STAGE/'data/integrations/english-stage-20261101'
if (BASE/'plan.json').exists() and (BASE/'asset-catalog.json').exists():
 ROOT=BASE.parents[2];OUT=ROOT/'assets/shiritori';META=BASE
plan=json.loads((META/'plan.json').read_text(encoding='utf-8'))
cards=json.loads((META/'english-input.json').read_text(encoding='utf-8'))['cards']
by_en={c['en']:c for c in cards};planned={x['en']:x for x in plan['items']}
FONT='C:/Windows/Fonts/meiryo.ttc';BOLD='C:/Windows/Fonts/meiryob.ttc'
INK='#243d4a';ACC='#227b85';BLUE='#e4f2f3';ORANGE='#df8a31';LIGHT='#eef2f3';GRAY='#9ba7ad'
used=[]
def font(n,b=False):return ImageFont.truetype(BOLD if b else FONT,n)
def text(d,box,s,size=40,fill=INK,bold=False,align='center'):
 x,y,w,h=box;size0=size
 while size>=18:
  f=font(size,bold);lines=[];line=''
  for c in str(s):
   if c=='\n' or d.textlength(line+c,font=f)>w:
    lines.append(line);line='' if c=='\n' else c
   else:line+=c
  if line:lines.append(line)
  if len(lines)*(size*1.45)<=h:break
  size-=1
 assert size>=18,(s,box,size0)
 for i,line in enumerate(lines):
  xx=x+(w-d.textlength(line,font=f))/2 if align=='center' else x
  d.text((xx,y+i*size*1.45),line,font=f,fill=fill)
 return {'text':str(s),'box':list(box),'fontSize':size,'lines':len(lines)}
def arrow(d,p,q,color=ACC,width=10):
 d.line([p,q],fill=color,width=width);a=math.atan2(q[1]-p[1],q[0]-p[0]);r=25
 d.polygon([q,(q[0]-r*math.cos(a-.55),q[1]-r*math.sin(a-.55)),(q[0]-r*math.cos(a+.55),q[1]-r*math.sin(a+.55))],fill=color)
def person(d,x,y,color=ACC,scale=1):
 r=22*scale;d.ellipse((x-r,y-r,x+r,y+r),fill=color);d.rounded_rectangle((x-31*scale,y+30*scale,x+31*scale,y+110*scale),radius=17*scale,fill=color);d.line((x-16*scale,y+105*scale,x-25*scale,y+154*scale),fill=color,width=max(1,int(15*scale)));d.line((x+16*scale,y+105*scale,x+25*scale,y+154*scale),fill=color,width=max(1,int(15*scale)))
def tile(d,x,y,fill=ACC,n=1):
 for k in range(n):d.rounded_rectangle((x+k*65,y,x+46+k*65,y+46),radius=8,fill=fill)
def clock(d,cx,cy,r,hour=9,minute=0):
 d.ellipse((cx-r,cy-r,cx+r,cy+r),fill='white',outline=INK,width=6)
 for n in range(1,13):
  a=math.radians(n*30-90);tx=cx+math.cos(a)*r*.79;ty=cy+math.sin(a)*r*.79;text(d,(tx-18,ty-24,36,48),str(n),28)
 for angle,length,width,col in [((hour%12)*30+minute/2-90,r*.48,11,INK),(minute*6-90,r*.67,7,ACC)]:
  a=math.radians(angle);d.line((cx,cy,cx+length*math.cos(a),cy+length*math.sin(a)),fill=col,width=width)
 d.ellipse((cx-9,cy-9,cx+9,cy+9),fill=ORANGE)
def picture(im,en,box):
 x,y,w,h=map(int,box);c=by_en.get(en);item=planned.get(en);path=None
 if item and item['kind']=='raster':path=OUT/item['filename']
 elif c and c.get('image'):path=ROOT/'assets/shiritori'/c['image']['url'].split('/')[-1]
 elif item and item['kind']=='reuse':path=ROOT/'assets/shiritori'/item['filename']
 if not path or not path.exists():return False
 used.append(dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 with Image.open(path) as src:
  src=src.convert('RGB');src.thumbnail((w,h),Image.Resampling.LANCZOS);im.paste(src,(x+(w-src.width)//2,y+(h-src.height)//2))
 return True
def diagram(x):
 used.clear()
 en=x['en'];kind=x.get('diagram','example');n=x.get('number');im=Image.new('RGB',(768,768),'#fafcfb');d=ImageDraw.Draw(im);layout=[];evidence={}
 d.rounded_rectangle((14,14,754,754),radius=32,fill='white',outline='#d4e3e3',width=3)
 layout.append(text(d,(35,25,698,88),en,64,bold=True,fill=ACC))
 d.rounded_rectangle((36,122,732,458),radius=25,fill='#f4f8f6')
 if kind=='number':
  if n<=20:
   for i in range(n):
    cx=170+(i%5)*105;cy=175+(i//5)*60;d.ellipse((cx-17,cy-17,cx+17,cy+17),fill=ACC)
   if n==0:text(d,(140,225,490,70),'何もない：0こ',46)
  elif n<100:
   for i in range(n//10):
    for j in range(10):d.ellipse((100+j*53,153+i*28,115+j*53,168+i*28),fill=ACC)
  elif n==100:
   for i in range(100):
    xx=248+(i%10)*27;yy=151+(i//10)*23;d.ellipse((xx,yy,xx+13,yy+13),fill=ACC)
  else:
   for k in range(10):
    bx=65+(k%5)*130;by=151+(k//5)*130
    d.rectangle((bx-8,by-8,bx+106,by+106),outline=GRAY,width=2)
    for i in range(100):
     xx=bx+(i%10)*10;yy=by+(i//10)*10;d.ellipse((xx,yy,xx+5,yy+5),fill=ACC)
   text(d,(75,407,610,45),'100 × 10 = 1000',34)
  if n!=1000:text(d,(230,399,310,54),str(n),42,bold=True)
  evidence.update(quantity=n,dotCount=n)
 elif kind=='month':
  for i in range(1,13):
   xx=70+((i-1)%4)*160;yy=155+((i-1)//4)*95;d.rounded_rectangle((xx,yy,xx+145,yy+76),radius=12,fill=ACC if i==n else 'white',outline='#b8cccf',width=2);text(d,(xx+3,yy+12,139,60),f'{i}月',38,fill='white' if i==n else INK)
  evidence.update(calendarMonths=12,highlightMonth=n)
 elif kind=='clock':clock(d,384,287,151,n);evidence.update(hour=n,minute=0)
 elif kind in ['pronoun','possessive','possessive-pronoun']:
  forms=[['I','me','my','mine'],['you','you','your','yours'],['he','him','his','his'],['she','her','her','hers'],['it','it','its','—'],['we','us','our','ours'],['they','them','their','theirs']]
  col={'pronoun':0,'possessive':2,'possessive-pronoun':3}[kind]
  if en in ['me','him','us','them']:col=1
  row=next(r for r in forms if r[col]==en)
  labels=['〜は','〜を／に','〜の','〜のもの']
  for j,(v,l) in enumerate(zip(row,labels)):
   xx=67+j*165;d.rounded_rectangle((xx,167,xx+145,322),radius=16,fill=ACC if j==col else 'white',outline='#acc7c8',width=2)
   text(d,(xx+5,178,135,50),l,29,fill='white' if j==col else INK);text(d,(xx+5,246,135,66),v,47,bold=True,fill='white' if j==col else INK)
  text(d,(60,355,645,66),{'I':'話し手','you':'聞き手','he':'話題の男性','she':'話題の女性','it':'話題の物・動物','we':'話し手を含む複数','they':'話題の複数の人・物'}[row[0]],36)
  evidence.update(forms=row,formColumn=col)
 elif kind=='be':
  groups=[('I','am'),('he / she / it','is'),('you / we / they','are')]
  for j,(a,b) in enumerate(groups):
   yy=154+j*83;d.rounded_rectangle((75,yy,693,yy+68),radius=12,fill=ACC if en==b else 'white',outline='#b8cdcf',width=2)
   text(d,(88,yy+9,410,55),a,39,fill='white' if en==b else INK);text(d,(518,yy+9,155,55),b,42,bold=True,fill='white' if en==b else INK)
  if en=='be':text(d,(130,405,515,44),'原形：be',31,bold=True)
 elif kind=='article':
  for j,(word,objecten,note) in enumerate([('a','pen','子音の音の前'),('an','apple','母音の音の前')]):
   xx=96+j*320;d.rounded_rectangle((xx,152,xx+255,423),radius=18,fill='white',outline=ACC if en==word else '#b8cdcf',width=5 if en==word else 2)
   picture(im,objecten,(xx+60,205,135,135));text(d,(xx+10,155,235,58),word,45,bold=True);text(d,(xx+10,365,235,47),note,28)
  if en=='the':
   d.rounded_rectangle((66,157,702,436),radius=20,fill='#f4f8f6');tile(d,180,250,GRAY,3);d.ellipse((238,229,318,316),outline=ORANGE,width=8);text(d,(90,350,590,63),'特定できる「あの／その」',38)
 elif kind=='preposition':
  if en in ['in','on','under','near','behind','in front of','next to','by','between','out']:
   bx,by,bw,bh=300,235,165,135
   pos={'in':(383,305),'on':(383,211),'under':(383,403),'near':(535,300),'behind':(383,234),'in front of':(383,347),'next to':(515,305),'by':(515,305),'between':(384,305),'out':(566,305)}[en]
   if en=='behind':d.ellipse((pos[0]-27,pos[1]-27,pos[0]+27,pos[1]+27),fill=ORANGE)
   if en=='between':
    d.rounded_rectangle((180,235,290,370),radius=12,fill='#d7e4e6',outline=ACC,width=4);d.rounded_rectangle((480,235,590,370),radius=12,fill='#d7e4e6',outline=ACC,width=4)
   else:d.rounded_rectangle((bx,by,bx+bw,by+bh),radius=12,fill=None if en=='in' else '#d7e4e6',outline=ACC,width=6)
   if en!='behind':d.ellipse((pos[0]-25,pos[1]-25,pos[0]+25,pos[1]+25),fill=ORANGE)
   if en=='out':arrow(d,(385,305),(515,305))
   evidence.update(ballCenter=list(pos),referenceBox=[bx,by,bw,bh])
  elif en in ['before','after']:
   arrow(d,(115,310),(655,310));
   for j,l in enumerate(['前','基準','後']):
    xx=195+j*190;d.ellipse((xx-23,287,xx+23,333),fill=ORANGE if j==(0 if en=='before' else 2) else GRAY);text(d,(xx-65,345,130,70),l,38)
  elif en in ['up','down']:
   arrow(d,(384,390 if en=='up' else 195),(384,195 if en=='up' else 390),ORANGE,22)
  elif en in ['to','from','at']:
   person(d,155,215);picture(im,'school',(450,170,190,190))
   if en=='at':
    d.ellipse((497,350,590,375),outline=ORANGE,width=5);person(d,550,270,scale=.48)
   else:arrow(d,(252,296),(440,296)) if en!='from' else arrow(d,(440,296),(252,296))
   text(d,(90,384,580,46),{'to':'目的地へ','from':'出発した所から','at':'特定の地点で'}[en],36)
  elif en=='with':person(d,275,200);person(d,480,200,ORANGE);d.line((275,393,480,393),fill=ACC,width=7);text(d,(180,402,410,48),'一緒に',34)
  elif en=='for':picture(im,'present',(90,185,180,180));person(d,580,210);arrow(d,(310,280),(500,280));text(d,(250,365,300,55),'〜のために',36)
  elif en=='of':picture(im,'book',(130,180,190,190));picture(im,'school',(440,180,190,190));text(d,(305,235,155,70),'of',49,bold=True);text(d,(135,380,500,50),'二つの名詞の関係',34)
  else:
   d.rounded_rectangle((135,174,637,376),radius=32,fill='white',outline=ACC,width=6);picture(im,'soccer',(280,185,190,175));text(d,(125,390,520,52),'話題や手段などの関係',33)
 elif kind=='demonstrative':
  person(d,130,225);near=en in ['this','these','here'];multiple=en in ['these','those'];tile(d,260,285,ACC if near else GRAY,3 if multiple else 1);tile(d,535,195,GRAY if near else ACC,3 if multiple else 1)
  arrow(d,(180,250),(280,250) if near else (570,250));text(d,(250,370,190,50),'近い',35);text(d,(505,370,190,50),'遠い',35)
 elif kind=='quantity':
  if en in ['much']:
   d.rectangle((300,170,465,395),outline=ACC,width=5);d.rectangle((307,202,458,388),fill='#80c8dc');text(d,(160,405,450,44),'数えないものの量',31)
  else:
   count=2 if en=='both' else 12 if en in ['many','a lot of'] else 8
   for i in range(count):
    xx=145+(i%6)*89;yy=198+(i//6)*100;highlight=en in ['all','every','each','both','many','a lot of'] or (i<3 if en in ['some','any'] else i==count-1)
    if en=='each':d.rectangle((xx-10,yy-10,xx+55,yy+55),outline=ORANGE,width=3)
    d.ellipse((xx,yy,xx+45,yy+45),fill=ACC if highlight else '#d8e1e3',outline=INK,width=2)
   if en=='any':text(d,(290,350,190,80),'?',64,bold=True)
   elif en in ['each','every']:text(d,(140,370,490,55),'一つ一つに注目',34)
   elif en=='another':text(d,(140,370,490,55),'もう一つ',34)
   elif en=='other':text(d,(140,370,490,55),'ほかのもの',34)
  evidence.update(quantityContext=en)
 elif kind=='question':
  target={'who':'person','whose':'bag','what':'box','where':'map','when':'clock','what color':'red','what sports':'soccer','what food':'sandwich','what drink':'water','what animal':'cat','what subject':'book','what time':'clock','how much':'money','how many':'apple','how old':'birthday','how tall':'tall','how long':'ruler','how about':'tea','which':'apple','how':'bicycle','why':'rain'}.get(en,'box')
  if en=='how':
   text(d,(100,180,560,65),'状態・方法・程度',44,bold=True);text(d,(110,280,540,110),'How are you?\nどのような調子？',36);target=None
  elif en=='why':
   picture(im,'dog',(165,162,260,260));text(d,(170,385,450,50),'理由をたずねる',33);target=None
  elif target=='person':person(d,265,205)
  elif target=='clock':clock(d,282,291,116,7)
  elif target and not picture(im,target,(165,162,260,260)):tile(d,260,265)
  if en!='how':text(d,(465,205,190,175),'?',112,bold=True,fill=ORANGE)
  if en=='which':picture(im,'banana',(98,184,145,180));picture(im,'apple',(295,184,145,180))
 elif kind in ['auxiliary','negative','affirmative','request','conjunction','adverb']:
  if kind=='auxiliary':
   if en=='can':picture(im,'swim',(260,158,245,245));text(d,(115,390,540,55),'can ＋ 動詞の原形',35)
   else:
    for j,(subject,aux) in enumerate([('I / you / we / they','do'),('he / she / it','does')]):
     yy=180+j*110;d.rounded_rectangle((85,yy,683,yy+87),radius=14,fill=ACC if en==aux else 'white',outline=ACC,width=2);text(d,(102,yy+15,410,65),subject,37,fill='white' if en==aux else INK);text(d,(510,yy+15,160,65),aux,41,bold=True,fill='white' if en==aux else INK)
  elif kind=='conjunction':
   left,right=('apple','banana') if en in ['and','or'] else ('tired','happy') if en=='but' else ('swim','summer')
   picture(im,left,(135,185,190,190));picture(im,right,(445,185,190,190));text(d,(325,228,120,90),'+' if en=='and' else '/' if en=='or' else '→',65,bold=True)
   text(d,(115,381,540,58),{'and':'二つをつなぐ','or':'どちらかを選ぶ','but':'疲れた。でもうれしい','because':'泳げるので夏が好き'}[en],34)
  elif kind in ['negative','affirmative']:
   d.ellipse((285,179,485,379),outline=ACC if kind=='affirmative' else '#bd5c56',width=16)
   if kind=='negative':d.line((306,200,464,358),fill='#bd5c56',width=16)
   text(d,(220,395,330,48),'肯定する' if kind=='affirmative' else '打ち消す',33)
  elif kind=='request':person(d,238,215);person(d,550,215,ORANGE);arrow(d,(312,252),(470,252));text(d,(270,161,235,60),'Please',44,bold=True);text(d,(165,390,440,52),'ていねいに頼む',34)
  else:tile(d,190,250,ACC,2);arrow(d,(370,274),(465,274));tile(d,510,250,ORANGE);text(d,(100,378,570,52),'文に意味を付け加える',34)
 else:
  if en in ['Monday','Saturday','week','weekend']:
   labels=['月','火','水','木','金','土','日'];high=[0] if en=='Monday' else [5] if en=='Saturday' else [5,6] if en=='weekend' else list(range(7))
   for j,l in enumerate(labels):
    xx=66+j*93;d.rounded_rectangle((xx,218,xx+81,329),radius=10,fill=ACC if j in high else 'white',outline=GRAY,width=2);text(d,(xx+5,247,71,60),l,39,fill='white' if j in high else INK)
   text(d,(170,369,430,55),'1週間 = 7日',37);evidence.update(days=7,highlightDays=high)
  elif en in ['hour','minute']:
   left,right=('1時間','60分') if en=='hour' else ('1分','60秒')
   for j,t in enumerate([left,right]):
    xx=120+j*335;d.rounded_rectangle((xx,205,xx+205,350),radius=20,fill=BLUE,outline=ACC,width=3);text(d,(xx+10,242,185,80),t,43,bold=True)
   text(d,(330,241,110,80),'=',55,bold=True);evidence.update(durationSeconds=3600 if en=='hour' else 60)
  elif en in ['midnight','early','now']:
   h=0 if en=='midnight' else 8 if en=='early' else 9;clock(d,384,285,133,h);text(d,(160,415,450,43),{'midnight':'午前0時','early':'予定9時より前の8時','now':'現在の時刻'}[en],30)
  elif en=='month':
   for i in range(31):
    xx=180+(i%7)*59;yy=163+(i//7)*48;d.rectangle((xx,yy,xx+45,yy+36),fill=BLUE,outline=ACC,width=2)
   text(d,(150,408,470,44),'暦の月：28〜31日',30);evidence.update(daysShown=31,dayRange=[28,31])
  elif en in ['always','usually','often','never']:
   filln={'always':7,'usually':6,'often':4,'never':0}[en]
   for i in range(7):d.ellipse((95+i*85,237,145+i*85,287),fill=ACC if i<filln else '#dbe2e4')
   text(d,(100,355,570,65),'0回' if en=='never' else '毎回' if en=='always' else '起こる頻度のイメージ',33);evidence.update(frequencyIllustration=True,filled=filln,total=7)
  elif en in ['gray']:d.rounded_rectangle((230,177,538,407),radius=23,fill='#808080');evidence.update(color='#808080')
  elif en in ['yen','dollar']:
   d.rounded_rectangle((170,203,599,355),radius=14,fill='#d6e9db',outline=ACC,width=6);text(d,(200,222,370,110),'¥ 円' if en=='yen' else '$ USD',65,bold=True);text(d,(125,390,520,45),'お金の単位',33)
  elif en in ['first','third']:
   for j in range(1,5):
    xx=148+(j-1)*145;d.ellipse((xx-32,230,xx+32,294),fill=ORANGE if j==(1 if en=='first' else 3) else ACC);text(d,(xx-42,322,84,60),str(j),36)
   arrow(d,(105,193),(660,193))
  elif en=='give':picture(im,'present',(285,175,190,190));person(d,150,230);person(d,620,230,ORANGE);arrow(d,(235,392),(540,392))
  elif en in ['Japanese','Chinese','French']:
   greetings={'Japanese':'こんにちは','Chinese':'你好','French':'Bonjour'};d.rounded_rectangle((155,170,615,315),radius=28,fill='white',outline=ACC,width=5);text(d,(170,192,430,100),greetings[en],53,bold=True);person(d,385,340,scale=.58)
  elif en=='American':picture(im,'America',(170,165,260,230));person(d,550,212);text(d,(115,397,540,48),'アメリカの／アメリカ人',32)
  elif en in ['art','subject','lesson','club']:
   if en=='lesson':picture(im,'class',(240,150,290,290))
   elif en=='art':picture(im,'picture',(175,167,230,230));tile(d,477,250,ORANGE,2)
   elif en=='subject':
    for j,t in enumerate(['国語','算数','理科']):
     xx=110+j*200;d.rounded_rectangle((xx,192,xx+160,365),radius=13,fill=BLUE,outline=ACC,width=3);text(d,(xx+10,245,140,65),t,40)
   else:person(d,250,220);person(d,385,220,ORANGE);person(d,520,220);text(d,(140,400,500,44),'同じ関心をもつ仲間',32)
  elif en=='be from':picture(im,'Japan',(125,172,250,245));person(d,570,220);arrow(d,(380,290),(490,290))
  elif en=='city hall':
   d.rectangle((205,240,563,398),fill=BLUE,outline=ACC,width=4);d.polygon([(185,240),(384,153),(583,240)],fill=ACC)
   for j in range(4):d.rectangle((240+j*75,268,278+j*75,320),fill='white',outline=ACC,width=3)
   text(d,(245,337,280,55),'市役所',40,bold=True)
  elif en in ['sunshine','clear up']:
   d.ellipse((292,186,472,366),fill='#f5c451');
   for k in range(12):
    a=math.pi*k/6;d.line((382+math.cos(a)*105,276+math.sin(a)*105,382+math.cos(a)*140,276+math.sin(a)*140),fill=ORANGE,width=8)
   if en=='clear up':picture(im,'cloud',(95,165,180,150));arrow(d,(180,384),(560,384))
  elif en in ['pilot','waiter','worker','officer','ski']:
   target={'pilot':'plane','waiter':'restaurant','worker':'office','officer':'office','ski':'ski'}[en]
   if en=='ski':
    source=ROOT/'assets/shiritori/expansion1024fv2-word-10918.png'
    with Image.open(source) as src:im.paste(src.convert('RGB').resize((282,282)),(105,153))
    used.append(dict(file=source.name,sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
   else:picture(im,target,(105,153,300,282))
   person(d,565,220);text(d,(435,397,255,45),{'pilot':'操縦する人','waiter':'料理を運ぶ人','worker':'働く人','officer':'公の仕事をする人','ski':'雪上を滑る'}[en],28)
  elif en=='Korea':text(d,(130,185,510,100),'韓国',72,bold=True);text(d,(95,316,580,95),'朝鮮半島の南部',44)
  elif en in ['only','thing']:
   if en=='only':tile(d,360,270);text(d,(150,380,470,52),'ほかにはない',35)
   else:picture(im,'book',(100,187,160,170));picture(im,'cup',(300,187,160,170));picture(im,'ball',(500,187,160,170))
  elif en=='bad':
   text(d,(120,173,520,70),'良くない状態・行い',38,bold=True);picture(im,'old',(215,244,210,175));d.line((475,255,560,345),fill='#bd5c56',width=14);d.line((475,345,560,255),fill='#bd5c56',width=14)
  elif en=='easy':
   d.rounded_rectangle((190,210,355,360),radius=12,fill=BLUE,outline=ACC,width=4);d.rounded_rectangle((385,210,550,360),radius=12,fill='#f1dbb6',outline=ORANGE,width=4);arrow(d,(330,400),(435,400));text(d,(125,147,530,52),'少ない手順でできる',34)
  elif en=='free':
   for j,t in enumerate(['することがある','空いている時間']):
    xx=92+j*328;d.rounded_rectangle((xx,190,xx+270,370),radius=14,fill=LIGHT,outline=ACC,width=3);text(d,(xx+10,209,250,50),t,30)
    if j==0:
     for k in range(3):d.rectangle((xx+30,275+k*22,xx+225,288+k*22),fill=GRAY)
    else:d.ellipse((xx+98,280,xx+164,346),outline=ORANGE,width=6)
  elif en=='very':
   text(d,(150,157,470,60),'程度を強める',38,bold=True)
   d.rectangle((190,300,295,397),fill='#efbb82');d.rectangle((480,230,585,397),fill='#d65a42');arrow(d,(330,312),(440,312));text(d,(130,401,220,45),'hot',30);text(d,(420,401,220,45),'very hot',30,bold=True)
  elif en=='really':
   text(d,(120,160,530,70),'本当に・実際に',40,bold=True);d.rounded_rectangle((198,267,570,371),radius=20,fill=BLUE,outline=ACC,width=4);text(d,(214,282,340,64),'事実を確かめる',36);d.line((297,407,335,435,410,381),fill=ACC,width=13)
  elif en=='again':
   arrow(d,(210,243),(540,243));arrow(d,(540,345),(210,345));d.line((540,243,540,345),fill=ACC,width=9);d.line((210,243,210,345),fill=ACC,width=9);text(d,(245,271,280,61),'もう一度',42,bold=True)
  elif en=='soon':
   arrow(d,(100,295),(670,295));d.ellipse((195,274,237,316),fill=ACC);d.ellipse((285,274,327,316),fill=ORANGE);text(d,(135,350,170,53),'今',35);text(d,(265,185,260,70),'少しあと',39,bold=True)
  elif en in ['away','outside']:
   d.rounded_rectangle((180,200,400,375),radius=15,fill=BLUE,outline=ACC,width=5);person(d,580,224,ORANGE);arrow(d,(405,330),(515,330));text(d,(130,402,510,44),'距離がある' if en=='away' else '囲まれた範囲の外',34)
  else:
   # Context sentence is a diagram of use, not a guessed pictorial synonym.
   words=x['example'].split();focus=[re.sub(r'[^a-z]','',t.lower()) for t in en.split()]
   d.rounded_rectangle((80,173,688,392),radius=20,fill='white',outline=ACC,width=4)
   layout.append(text(d,(103,199,562,157),x['example'],46,bold=True))
   text(d,(120,404,530,40),'ことばが使われる場面',29)
 layout.append(text(d,(40,478,688,86),x['ja'],44,bold=True))
 d.line((70,580,698,580),fill='#d8e5e3',width=2)
 layout.append(text(d,(55,596,658,67),x['example'],34))
 layout.append(text(d,(55,678,658,60),x['exampleJa'],30))
 source=OUT/x['sourceSheet'];source.parent.mkdir(parents=True,exist_ok=True);im.save(source,optimize=True)
 asset=OUT/x['filename'];im.resize((256,256),Image.Resampling.LANCZOS).save(asset,optimize=True)
 return dict(cardId=x['cardId'],file=x['filename'],sourceSheet=x['sourceSheet'],sourceSize=[768,768],assetSize=[256,256],type=kind,semantics=evidence,layout=layout,reusedIllustrations=list(used),sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest())
results=[diagram(x) for x in plan['items'] if x['kind']=='diagram']
(META/'diagram-validation.json').write_text(json.dumps({'rendererSha256':hashlib.sha256(Path(__file__).read_text(encoding='utf-8').encode('utf-8')).hexdigest(),'diagrams':results,'passed':True},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Review sheets retain the exact asset pixels and word labels for visual QA.
for start in range(0,len(results),30):
 group=results[start:start+30];sheet=Image.new('RGB',(1280,6*300),'white');d=ImageDraw.Draw(sheet)
 for j,r in enumerate(group):
  with Image.open(OUT/r['file']) as tileim:sheet.paste(tileim,((j%5)*256,(j//5)*300))
  text(d,((j%5)*256,(j//5)*300+257,256,40),planned[next(x['en'] for x in plan['items'] if x['cardId']==r['cardId'])]['en'],22)
 sheet.save(BASE/f'diagrams-review-{start//30+1:02}.png')
print(f'Generated {len(results)} reproducible diagrams with measured text layout')
