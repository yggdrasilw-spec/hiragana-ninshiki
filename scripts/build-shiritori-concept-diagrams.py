"""Draw exact mathematical/quantity diagrams as new PNG assets (no generated-image edits)."""
import json, math, argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
STAGE=Path(__file__).resolve().parent
OUT=STAGE/'native'
S=768
BLUE='#2384ba'; ORANGE='#f3a647'; INK='#263c4e'; BG='#fffdf5'; PALE='#e2f0f5'
FONT='C:/Windows/Fonts/meiryo.ttc'
def font(n): return ImageFont.truetype(FONT,n)
def line(d,xy,color=INK,width=6): d.line(xy,fill=color,width=width)
def txt(d,p,s,n=42,color=INK): d.text(p,s,font=font(n),fill=color)
def arrow(d,p,q,color=BLUE,width=9,both=False):
    line(d,[p,q],color,width)
    ang=math.atan2(q[1]-p[1],q[0]-p[0]); size=24
    def tip(at,a): d.polygon([at,(at[0]-size*math.cos(a-.5),at[1]-size*math.sin(a-.5)),(at[0]-size*math.cos(a+.5),at[1]-size*math.sin(a+.5))],fill=color)
    tip(q,ang)
    if both: tip(p,ang+math.pi)
def dot(d,x,y,r=24,color=BLUE): d.ellipse((x-r,y-r,x+r,y+r),fill=color,outline=INK,width=4)
def rect(d,box,color=BLUE): d.rounded_rectangle(box,radius=8,fill=color,outline=INK,width=6)
def dots(d,n,origin=(100,280),color=BLUE,spacing=72,cols=6):
    for i in range(n): x,y=origin[0]+i%cols*spacing,origin[1]+i//cols*spacing; dot(d,x,y,24,color)

# These diagrams have precise counts, directions and proportions. All other concepts
# remain concrete scene illustrations in the image-generation sheets.
KINDS={
 'trolley':'トロッコ問題',
 'frequency':'高周波', 'third':'三分',
 'mechanism':'仕組み', 'honorific':'様付け',
 'centrifugal':'遠心 遠心力', 'extend':'延長',
 'chlorination':'塩化',
 'spiral':'螺旋', 'dot':'点 印', 'one':'一 一個', 'two':'二杯', 'three':'三度', 'layers':'二層',
 'colour':'色 濃緑 焦げ茶 太白',
 'gravity':'引力',
 'half':'半分', 'fraction':'分数 一分 一部', 'division':'割り算', 'ratio':'割合 率',
 'addition':'足す プラス 演算', 'factors':'因数', 'log':'対数',
 'count':'数える 計数 数量', 'more':'多い 大量 沢山 最多', 'few':'少し 少々 ちょっと',
 'all':'全て 一切 有った丈', 'sum':'累計', 'volume':'体積',
 'length':'長さ 長い 寸法 丈', 'height':'高さ 高い', 'depth':'深さ',
 'size':'大きい 大きさ 小さい', 'near':'近い', 'far':'遠い 遠く 距離',
 'interval':'間隔', 'diagonal':'斜め 傾斜', 'shape':'形状', 'arc':'円弧', 'circumference':'円周',
 'cycle':'一周 回転 円転', 'centre':'中心', 'middle':'中間', 'around':'周り',
 'next':'次 次々 一番 番 最後 最終 最初', 'parts':'各々 類 クラスター', 'same':'同じ 共通 一致 類似 類似性',
 'different':'別', 'empty':'空 空っぽ 空く 空白 空欄 空洞 虚ろ', 'below':'以下', 'except':'以外',
 'minus':'差 差し引き', 'decline':'減少', 'double':'重複', 'thick':'厚い 薄い', 'surface':'一面',
 'solid':'固体', 'liquid':'えき 液 えき体 液体', 'gas':'気体 水じょう気',
 'acid':'酸性', 'alkali':'アルカリ性', 'milk':'乳白色', 'zigzag':'ギザギザ', 'none':'無い',
}
LOOKUP={w:k for k,words in KINDS.items() for w in words.split()}

def draw(word,kind):
    im=Image.new('RGB',(S,S),BG); d=ImageDraw.Draw(im)
    txt(d,(45,28),word,62)
    if kind in {'half','fraction','ratio'}:
        if kind=='half':
            d.pieslice((140,170,628,658),90,270,fill=ORANGE,outline=INK,width=7)
            d.pieslice((140,170,628,658),270,450,fill=PALE,outline=INK,width=7)
            line(d,[(384,170),(384,658)])
            txt(d,(90,690),'同じ大きさに２つ',45)
        else:
            for i in range(4): rect(d,(90+i*145,270,235+i*145,540),ORANGE if i<(3 if kind=='ratio' else 1) else PALE)
            txt(d,(135,585),'3 / 4' if kind=='ratio' else '1 / 4',80)
            if kind=='ratio': txt(d,(115,690),'全体とくらべる',43)
    elif kind=='division':
        txt(d,(145,150),'6 ÷ 3 = 2',68)
        for col in range(3):
            d.rounded_rectangle((45+col*240,290,265+col*240,590),20,fill=PALE,outline=INK,width=5)
            dot(d,150+col*240,365);dot(d,150+col*240,510)
        txt(d,(80,650),'３つに同じ数ずつ',43)
    elif kind=='addition':
        dots(d,2,(125,300));txt(d,(290,265),'+',70);dots(d,3,(430,300),ORANGE)
        arrow(d,(384,390),(384,470));dots(d,5,(220,550),cols=5,spacing=80)
        txt(d,(160,650),'2 + 3 = 5',75)
    elif kind=='factors':
        for y in range(3):
            for x in range(4): dot(d,225+x*80,280+y*85)
        arrow(d,(165,240),(165,485),both=True);txt(d,(80,325),'3',64)
        arrow(d,(185,545),(510,545),both=True);txt(d,(325,565),'4',64)
        txt(d,(135,660),'3 × 4 = 12',66)
    elif kind=='log':
        txt(d,(135,155),'2³ = 8',85);txt(d,(135,260),'log₂ 8 = 3',70)
        for n,y in [(1,530),(2,465),(4,400),(8,335)]:
            x=85+n*70;dot(d,x,y,14);txt(d,(x-15,570),str(n),37)
        line(d,[(110,610),(680,610)]);line(d,[(110,610),(110,345)])
    elif kind in {'count','more','few','all','sum','parts'}:
        if kind=='sum':
            dots(d,2,(110,210));txt(d,(330,180),'+',60);dots(d,3,(470,210),ORANGE)
            arrow(d,(375,300),(375,410));dots(d,5,(165,520),spacing=100,cols=5);txt(d,(230,650),'合計 5',65)
        elif kind=='parts' and word=='各々':
            for i,c in enumerate([BLUE,ORANGE,'#67a469']):
                d.rounded_rectangle((45+i*240,240,265+i*240,615),20,fill=PALE,outline=INK,width=5)
                dot(d,155+i*240,420,58,c)
            txt(d,(170,660),'それぞれ ひとつずつ',37)
        elif kind=='parts':
            for x in [185,570]:
                d.ellipse((x-145,220,x+145,650),fill=PALE,outline=INK,width=5)
                for j in range(3): dot(d,x,300+j*130,35,BLUE if x==185 else ORANGE)
        elif kind=='few':
            dots(d,12,(140,215),color='#d9e1e6',cols=6,spacing=90)
            dots(d,2,(295,515),spacing=140)
            txt(d,(285,650),'少し',60)
        elif kind=='more' and word=='最多':
            for col,n in enumerate([3,6,12]):
                x=100+col*240
                d.rounded_rectangle((x-55,185,x+155,635),20,fill=PALE,outline=ORANGE if n==12 else INK,width=9 if n==12 else 4)
                dots(d,n,(x,235),color=ORANGE if n==12 else BLUE,spacing=65,cols=2)
                txt(d,(x,655),str(n),58)
        else:
            n=12 if kind in {'more','all'} else 6;dots(d,n,(175,285),spacing=90,cols=5)
            if kind=='count': txt(d,(170,560),'1  2  3  4  5  6',43)
            if kind=='all': d.rounded_rectangle((110,190,660,550),radius=35,outline=ORANGE,width=10);txt(d,(240,610),'ぜんぶ',68)
    elif kind in {'length','size','height','thick'}:
        if kind=='height':
            rect(d,(180,410,315,650),PALE);rect(d,(450,190,585,650),BLUE)
            arrow(d,(650,190),(650,650),both=True);txt(d,(390,690),'下から上まで',43)
        elif kind=='thick':
            thick=word=='厚い';rect(d,(100,310,630,560),BLUE);rect(d,(100,220,630,270),ORANGE)
            arrow(d,(675,310 if thick else 220),(675,560 if thick else 270),both=True)
        elif kind=='size':
            rect(d,(95,450,275,630),ORANGE);rect(d,(365,200,665,500),BLUE)
        else:
            rect(d,(100,250,670,315),BLUE);rect(d,(100,470,330,535),ORANGE)
            arrow(d,(100,385),(670,385),both=True);txt(d,(260,570),'端から端まで',45)
    elif kind=='depth':
        rect(d,(155,190,560,650),PALE);line(d,[(145,270),(570,270)],BLUE,10)
        arrow(d,(625,275),(625,645),both=True);txt(d,(125,680),'水面から底まで',43)
    elif kind=='volume':
        d.polygon([(210,255),(480,185),(630,340),(360,410)],fill='#9bcbdc',outline=INK,width=7)
        d.polygon([(210,255),(360,410),(360,675),(210,530)],fill='#3c96bc',outline=INK,width=7)
        d.polygon([(360,410),(630,340),(630,595),(360,675)],fill='#68b4c9',outline=INK,width=7)
        txt(d,(150,120),'立体の大きさ',48)
    elif kind in {'near','far','interval'}:
        x2=360 if kind=='near' else 640
        dot(d,150,450,60,ORANGE);dot(d,x2,450,60,BLUE)
        arrow(d,(150,590),(x2,590),both=True)
        txt(d,(170,650),'あいだの長さ',49)
    elif kind=='diagonal':
        line(d,[(100,630),(670,630)],'#a9b6ba',5);line(d,[(130,600),(635,240)],BLUE,22)
        d.arc((80,355,440,715),300,360,fill=ORANGE,width=12)
    elif kind in {'arc','circumference','cycle','centre','middle','around'}:
        if kind=='middle':
            rect(d,(90,300,230,570),PALE);rect(d,(300,300,440,570),ORANGE);rect(d,(510,300,650,570),PALE)
        else:
            box=(150,200,620,670);d.ellipse(box,outline=INK,width=8)
            if kind=='centre':dot(d,385,435,28,ORANGE);arrow(d,(200,150),(365,410),ORANGE)
            elif kind=='arc':d.arc(box,215,325,fill=ORANGE,width=30)
            elif kind=='circumference':d.ellipse(box,outline=ORANGE,width=18);txt(d,(225,120),'まわりの長さ',43)
            elif kind=='around':
                for i in range(8): ang=i*math.pi/4;dot(d,385+270*math.cos(ang),435+270*math.sin(ang),18,ORANGE)
            else:
                d.arc(box,15,345,fill=BLUE,width=14);arrow(d,(595,485),(617,415));dot(d,385,435,16)
    elif kind=='next':
        for i in range(4):
            highlight=(i==0 and word in {'一番','最初'}) or (i==1 and word=='次') or (i==3 and word in {'最後','最終'})
            rect(d,(40+i*180,305,185+i*180,520),ORANGE if highlight else BLUE);txt(d,(70+i*180,355),str(i+1),63,'#ffffff')
        arrow(d,(100,620),(650,620));txt(d,(230,670),'順番に',55)
    elif kind in {'same','different','double'}:
        if word=='共通':
            dot(d,195,420,100,BLUE)
            d.polygon([(455,530),(555,295),(655,530)],fill=BLUE,outline=INK,width=7)
            txt(d,(185,630),'同じ色が共通',48)
        elif word in {'類似','類似性'}:
            rect(d,(100,300,290,520),BLUE);rect(d,(435,320,650,515),'#60a9c7')
            txt(d,(315,350),'≈',75);txt(d,(220,630),'よく似ている',48)
        else:
            rect(d,(100,300,290,520),BLUE);rect(d,(455,300,645,520),ORANGE if kind=='different' else BLUE)
            txt(d,(325,350),'≠' if kind=='different' else '=',70)
        if kind=='double':txt(d,(200,600),'同じものが２つ',47)
    elif kind=='shape':
        d.polygon([(100,580),(230,240),(350,580)],fill=BLUE,outline=INK,width=7)
        rect(d,(440,260,650,550),ORANGE);dot(d,570,640,55)
    elif kind=='empty':
        if word in {'空白','空欄'}:
            rect(d,(135,180,635,635),BG)
            for y in [260,480,550]:line(d,[(205,y),(565,y)],'#97a9ae',8)
            d.rectangle((200,325,570,420),outline=ORANGE,width=8)
            txt(d,(175,670),'何も書いていない所',39)
        else:
            rect(d,(165,215,610,620),PALE);d.rounded_rectangle((225,285,550,555),15,fill=BG,outline=INK,width=7)
            txt(d,(210,660),'中には何もない',42)
    elif kind=='below':
        txt(d,(200,140),'3 以下',65)
        for n in range(1,5):dot(d,120+n*130,410,48,BLUE if n<=3 else '#c4c9ce');txt(d,(98+n*130,475),str(n),56)
        line(d,[(200,590),(550,590)],ORANGE,12)
    elif kind=='except':
        rect(d,(115,210,635,625),PALE)
        for x,y in [(250,360),(490,360),(250,510),(490,510)]:dot(d,x,y,48,ORANGE if (x,y)==(250,360) else BLUE)
        d.ellipse((175,285,325,435),outline=ORANGE,width=9);line(d,[(175,435),(325,285)],ORANGE,9)
        txt(d,(200,655),'これを除いたもの',37)
    elif kind in {'minus','decline'}:
        dots(d,5,(190,280),spacing=90,cols=5)
        if kind=='minus':
            for i in range(2):line(d,[(425+i*90,245),(495+i*90,315)],ORANGE,10)
            txt(d,(150,560),'5 − 2 = 3',70)
        else: arrow(d,(375,390),(375,485));dots(d,2,(280,570),spacing=125)
    elif kind in {'solid','liquid','gas'}:
        txt(d,(160,115),'粒のならびのイメージ',36)
        if kind=='solid':
            for y in range(4):
                for x in range(4):dot(d,225+x*85,275+y*85,26)
            txt(d,(125,670),'形・体積がほぼ一定',40)
        else:
            line(d,[(120,230),(120,600),(650,600),(650,230)],INK,8)
            if kind=='liquid':
                d.rectangle((126,380,644,594),fill=PALE)
                for x,y in [(190,440),(275,435),(370,430),(465,450),(565,435),(180,540),(275,545),(375,525),(465,550),(575,535)]:dot(d,x,y,25)
                line(d,[(126,380),(644,380)],BLUE,8)
                txt(d,(135,670),'容器に合わせた形',42)
            else:
                for x,y in [(190,290),(425,260),(575,315),(310,375),(195,495),(450,480),(570,560)]:dot(d,x,y,20)
                txt(d,(95,670),'広がる・体積も変わる',40)
    elif kind in {'acid','alkali'}:
        before=BLUE if kind=='acid' else '#d6545a';after='#d6545a' if kind=='acid' else BLUE
        rect(d,(100,215,265,535),before);arrow(d,(300,370),(465,370));rect(d,(505,215,670,535),after)
        txt(d,(130,130),'リトマス紙の変化',47)
        txt(d,(75,600),'青 → 赤' if kind=='acid' else '赤 → 青',65)
    elif kind=='milk':
        rect(d,(215,180,550,620),'#f6f8f6');d.rectangle((223,335,542,609),fill='#fffefd')
        line(d,[(223,335),(542,335)],'#b4c8d1',5)
        txt(d,(205,665),'牛乳のような白',45)
    elif kind=='zigzag':
        line(d,[(80,580),(150,250),(220,580),(290,250),(360,580),(430,250),(500,580),(570,250),(640,580),(710,250)],BLUE,20)
    elif kind=='none':
        d.rounded_rectangle((145,240,635,640),30,fill=PALE,outline=INK,width=7)
        d.ellipse((280,330,500,550),outline='#d6545a',width=12)
        line(d,[(310,365),(475,510)],'#d6545a',12)
        txt(d,(230,665),'ここには無い',46)
    elif kind=='trolley':
        # Schematic thought experiment: five people versus one; no injury depicted.
        for dx in [-18,18]:
            line(d,[(385+dx,680),(385+dx,430),(145+dx,215)],INK,7)
            line(d,[(385+dx,430),(625+dx,215)],INK,7)
        rect(d,(335,530,435,625),PALE);arrow(d,(385,535),(385,465),BLUE,10)
        for i in range(5):
            x=85+i*67;dot(d,x,130,15,BLUE);rect(d,(x-13,151,x+13,201),BLUE)
        dot(d,625,130,15,ORANGE);rect(d,(612,151,638,201),ORANGE)
        txt(d,(170,50),'５人',42);txt(d,(565,50),'１人',42)
        dot(d,550,490,14,INK);line(d,[(550,490),(595,435)],INK,10);dot(d,595,435,16,ORANGE)
        txt(d,(95,700),'どうする？',47)
    elif kind=='third':
        for i in range(3):d.pieslice((140,170,628,658),i*120-90,(i+1)*120-90,fill=ORANGE if i==0 else PALE,outline=INK,width=7)
        txt(d,(320,665),'1 / 3',60)
    elif kind=='frequency':
        for y,n,color in [(265,2,BLUE),(490,8,ORANGE)]:
            line(d,[(95,y),(675,y)],'#b5c1ca',3)
            points=[(100+i*560/400,y-55*math.sin(i/400*math.pi*2*n)) for i in range(401)]
            line(d,points,color,9)
        txt(d,(125,150),'低い周波数',45)
        txt(d,(125,375),'高い周波数',45)
        txt(d,(150,640),'同じ時間に多く振動',45)
    elif kind=='honorific':
        rect(d,(155,165,620,650),BG)
        txt(d,(235,340),'○○ 様',65)
        d.ellipse((460,340,605,450),outline=ORANGE,width=8)
        txt(d,(200,680),'名前に「様」をつける',38)
    elif kind=='mechanism':
        for x,color in [(230,BLUE),(505,ORANGE)]:
            points=[]
            for i in range(96):
                a=i/96*math.pi*2;r=145 if i%4 in {1,2} else 120
                points.append((x+r*math.cos(a),390+r*math.sin(a)))
            d.polygon(points,fill=color,outline=INK,width=5);dot(d,x,390,18,BG)
        arrow(d,(145,195),(315,195),BLUE,13)
        arrow(d,(590,195),(420,195),ORANGE,13)
        txt(d,(140,620),'歯車がかみ合って動く',44)
    elif kind=='centrifugal':
        d.ellipse((170,180,600,610),outline=BLUE,width=8)
        dot(d,385,395,15,INK);dot(d,600,395,35,ORANGE)
        arrow(d,(605,395),(720,395),ORANGE,14)
        d.arc((160,170,610,620),215,320,fill=BLUE,width=13)
        arrow(d,(540,202),(570,245),BLUE,10)
        txt(d,(125,660),'回転する立場で見る力',43)
    elif kind=='extend':
        rect(d,(120,220,420,290),BLUE)
        arrow(d,(350,345),(350,435),ORANGE,12)
        rect(d,(120,490,650,560),BLUE)
        line(d,[(420,465),(420,595)],ORANGE,6)
        txt(d,(195,650),'長さをのばす',55)
    elif kind=='chlorination':
        txt(d,(80,180),'例：ナトリウムと塩素',48)
        txt(d,(85,320),'2 Na + Cl₂',68)
        arrow(d,(280,445),(480,445),ORANGE,14)
        txt(d,(165,530),'2 NaCl',72)
        txt(d,(155,650),'塩化ナトリウム',48)
    elif kind=='spiral':
        points=[]
        for i in range(500):
            a=i/499*math.pi*6;r=20+i/499*260
            points.append((384+r*math.cos(a),405+r*math.sin(a)))
        line(d,points,BLUE,12)
    elif kind in {'dot','one','two','three'}:
        n={'dot':1,'one':1,'two':2,'three':3}[kind]
        if kind=='two':
            for x in [170,435]:
                rect(d,(x,280,x+135,540),BG)
                d.arc((x+95,310,x+200,480),270,90,fill=INK,width=9)
        else:dots(d,n,origin=(210,400),spacing=170,cols=3)
        if kind=='two':txt(d,(220,620),'２つの杯',55)
        elif kind=='three':txt(d,(160,620),'１回　２回　３回',45)
        else:txt(d,(230,620),'１つ',55)
    elif kind=='layers':
        n=2 if word=='二層' else 3
        for i in range(n):rect(d,(150,240+110*i,620,325+110*i),[BLUE,ORANGE,PALE][i])
    elif kind=='colour':
        if word=='色':
            for i,c in enumerate(['#dd4444','#338dcc','#f0c443']):rect(d,(90+220*i,260,260+220*i,580),c)
        else:rect(d,(150,240,620,640),{'濃緑':'#164326','焦げ茶':'#583a29','太白':'#ffffff'}[word])
    elif kind=='gravity':
        d.ellipse((65,225,310,470),fill=BLUE,outline=INK,width=7)
        d.ellipse((590,280,710,400),fill='#bcc5cd',outline=INK,width=5)
        arrow(d,(330,315),(530,315),ORANGE,14)
        arrow(d,(575,395),(375,395),ORANGE,14)
        txt(d,(220,565),'互いを引く力',52)
    elif kind=='surface': rect(d,(150,200,620,650),BLUE)
    else: raise ValueError(kind)
    return im.resize((256,256),Image.Resampling.LANCZOS)

def main():
    global OUT
    ap=argparse.ArgumentParser()
    ap.add_argument('--plan',type=Path,default=STAGE/'requests.json' if (STAGE/'requests.json').exists() else STAGE.parent/'data/image-coverage/diagram-plan-2026-10-10.json')
    ap.add_argument('--output',type=Path,default=OUT)
    ap.add_argument('--preview-dir',type=Path,default=STAGE)
    args=ap.parse_args();OUT=args.output;OUT.mkdir(parents=True,exist_ok=True)
    args.preview_dir.mkdir(parents=True,exist_ok=True)
    req=json.loads(args.plan.read_text(encoding='utf-8'))
    native=[]
    for r in req:
        kind=LOOKUP.get(r['word'])
        if not kind:continue
        # 空 has another concrete sky row excluded in scope review.
        im=draw(r['word'],kind);im.save(OUT/r['filename'],optimize=True)
        native.append({**r,'kind':kind,'sourceType':'native-diagram','credit':'アプリ作成図','prompt':f"正確な数・割合・位置関係をコードで描いた図: {r['word']}。{r['meaning']}"})
    (args.preview_dir/'native-plan.json').write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for start in range(0,len(native),16):
        sheet=Image.new('RGB',(1024,1024),'white')
        for i,r in enumerate(native[start:start+16]):sheet.paste(Image.open(OUT/r['filename']),((i%4)*256,(i//4)*256))
        sheet.save(args.preview_dir/f'native-preview-{start//16+1:02}.png')
    print(json.dumps({'nativeDiagrams':len(native)}))
if __name__=='__main__':main()
