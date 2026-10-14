"""Create two new deterministic educational diagrams, without editing AI art."""
import json,math,io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/image-coverage/2026-10-14-expansion512-images'
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/meiryob.ttc',n)
def arrow(d,a,b,color,width=5):
    d.line([a,b],fill=color,width=width)
    x,y=b;ax,ay=a
    if y<ay:d.polygon([(x,y),(x-7,y+12),(x+7,y+12)],fill=color)
    elif x>ax:d.polygon([(x,y),(x-10,y-6),(x-10,y+6)],fill=color)
    else:d.polygon([(x,y),(x+10,y-6),(x+10,y+6)],fill=color)
def save(im,ident,scene):
    file=f'expansion512-oct14-diagram-word-{ident}.png'
    source=f'sheets/diagram-expansion512-oct14-word-{ident}.png'
    buffer=io.BytesIO();im.save(buffer,format='PNG');blob=buffer.getvalue()
    for path in [ROOT/'assets/shiritori'/file,ROOT/'assets/shiritori'/source]:
        if path.exists():assert path.read_bytes()==blob,'Never overwrite previous assets.'
        else:path.write_bytes(blob)
    return dict(filename=file,sourceSheet=source,cropValidation='',tileIndex=1,credit='プログラム生成図',scene=scene,prompt=scene)

im=Image.new('RGB',(256,256),'#fffaf0');d=ImageDraw.Draw(im)
d.text((128,24),'1 cm = 10 mm',font=font(22),fill='#153e67',anchor='mm')
# Exactly 10 minor intervals between the centimetre boundaries.
x0,x1,y=28,228,111
d.rounded_rectangle((15,96,241,162),radius=6,fill='#e9c989',outline='#8d6429',width=2)
for i in range(11):
    x=x0+20*i;d.line((x,y,x,y+(36 if i in (0,10) else 24 if i==5 else 16)),fill='#222',width=2)
d.line((x0,74,x1,74),fill='#246bb3',width=3)
d.line((x0,64,x0,88),fill='#246bb3',width=3);d.line((x1,64,x1,88),fill='#246bb3',width=3)
d.text((128,55),'1 cm',font=font(19),fill='#246bb3',anchor='mm')
d.line((x0,183,x0+20,183),fill='#d54326',width=3)
for x in (x0,x0+20):d.line((x,170,x,194),fill='#d54326',width=3)
d.text((48,219),'1 mm',font=font(20),fill='#d54326',anchor='mm')
milli=save(im,7575,'長さの模式図。隣り合う目盛りの間が1mm。10個の等間隔で1cmになる。画面上の実寸を測るための定規ではない。')

im=Image.new('RGB',(256,256),'#fff9ed');d=ImageDraw.Draw(im)
origin,size=20,24
d.rectangle((origin,20,origin+9*size,20+9*size),fill='#f0d296',outline='#805b33',width=2)
for i in range(1,9):
    d.line((origin+i*size,20,origin+i*size,236),fill='#a67944',width=1)
    d.line((origin,20+i*size,236,20+i*size),fill='#a67944',width=1)
center=lambda x,y:(origin+(x+.5)*size,20+(y+.5)*size)
king=center(4,1);rook=center(4,5)
arrow(d,(rook[0],rook[1]-13),(king[0],king[1]+14),'#dc432e',4)
d.ellipse((king[0]-18,king[1]-18,king[0]+18,king[1]+18),outline='#d43d2c',width=3)
def piece(x,y,text,down=False,color='#222'):
    cx,cy=center(x,y)
    points=[(cx-9,cy-10),(cx+9,cy-10),(cx+10,cy+6),(cx,cy+12),(cx-10,cy+6)] if down else [(cx-9,cy+10),(cx+9,cy+10),(cx+10,cy-6),(cx,cy-12),(cx-10,cy-6)]
    d.polygon(points,fill='#ffefbf',outline='#5f4529');d.text((cx,cy-1),text,font=font(16),fill=color,anchor='mm')
piece(4,1,'王',True,'#b92e22');piece(4,5,'飛');piece(7,8,'王',False,'#215f9a')
check=save(im,7597,'日本将棋連盟の駒の動き・王手の説明に基づく模式図。飛車と相手の王が同じ縦筋にあり、間に駒がなく、次に取れる形。自分の王は離れた位置。駒が成る場面ではない。')
check['sources']=['https://www.shogi.or.jp/knowledge/shogi/03.php','https://www.shogi.or.jp/knowledge/shogi/04.php']
im=Image.new('RGB',(256,256),'#f9fbff');d=ImageDraw.Draw(im)
d.rectangle((128,0,255,190),fill='#233351')
d.ellipse((17,16,43,42),fill='#ffbb37');d.ellipse((213,16,239,42),fill='#fff4b5');d.ellipse((220,10,246,35),fill='#233351')
for cx,hour in [(64,9),(192,1)]:
    cy=108;d.ellipse((cx-49,cy-49,cx+49,cy+49),fill='white',outline='#385575',width=3)
    for i in range(12):
        a=math.radians(30*i-90);x=cx+40*math.cos(a);y=cy+40*math.sin(a)
        d.ellipse((x-2,y-2,x+2,y+2),fill='#183957')
    # Exactly one minute hand and one shorter hour hand per face.
    d.line((cx,cy,cx,cy-32),fill='#183957',width=4)
    a=math.radians(hour*30-90)
    d.line((cx,cy,cx+23*math.cos(a),cy+23*math.sin(a)),fill='#183957',width=5)
    d.ellipse((cx-3,cy-3,cx+3,cy+3),fill='#183957')
d.text((64,169),'9:00',font=font(18),fill='#183957',anchor='mm')
d.text((192,169),'1:00',font=font(18),fill='white',anchor='mm')
d.text((128,220),'8時間の差',font=font(22),fill='#183957',anchor='mm')
zones=save(im,7544,'地域の時刻差の模式図。朝9:00と夜1:00の例は8時間差。各時計は時針と分針の2本で、分針はともに12を指す。特定の日付の特定都市の時刻表ではない。')
plan=json.loads((DIR/'plan.json').read_text(encoding='utf-8'))
for x in plan['items']:
    if x['id']==7575:x.update(milli)
    if x['id']==7597:x.update(check)
    if x['id']==7544:x.update(zones)
(DIR/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DIR/'precise-diagrams.json').write_text(json.dumps({'7575':milli,'7597':check,'7544':zones},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Created 3 new accurate diagrams: 10 ruler intervals, rook check and time difference.')
