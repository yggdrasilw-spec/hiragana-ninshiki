"""Reproduce exact number, calendar, language and geometry vocabulary examples."""
import json, math, hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/image-coverage/2026-10-13-wave10'
FONT='C:/Windows/Fonts/meiryo.ttc'
BLUE='#245b92';RED='#d7423b';GRAY='#566674'
def text(d,xy,s,size=42,fill=BLUE):
 f=ImageFont.truetype(FONT,size)
 while d.textbbox((0,0),s,font=f)[2]>680 and size>16:
  size-=1;f=ImageFont.truetype(FONT,size)
 d.text(xy,s,font=f,fill=fill,anchor='mm')
def line(d,a,b,fill=BLUE,width=7):d.line([a,b],fill=fill,width=width)
def arrow(d,a,b,fill=RED):
 line(d,a,b,fill);t=math.atan2(b[1]-a[1],b[0]-a[0])
 d.polygon([b,(b[0]-24*math.cos(t-.5),b[1]-24*math.sin(t-.5)),(b[0]-24*math.cos(t+.5),b[1]-24*math.sin(t+.5))],fill=fill)
EXAMPLES={236:['100円？ 200円？','いくらですか？'],327:['1 円','日本のお金'],345:['一 文','昔のお金の単位'],347:['1 里','昔の距離の単位'],371:['一 銭','昔のお金の単位'],381:['一丁目 │ 二丁目','町を分けた区画'],621:['apple → りんご','英語のテスト'],622:['Hello!','こんにちは'],626:['A B C D','a b c d'],632:['This is a dog.','これは犬です。'],893:['お名前は？','やまだ はなこ'],981:['あ → /a/','音を表す文字'],982:['さ・く・ら','音のひとまとまり'],1047:['あさの ひかり','♪ 歌う言葉 ♪'],1093:['（ 2 ＋ 3 ） × 4','括弧でくくる'],1094:['あ い う','印刷用の文字の型'],1106:['あ い う','ア イ ウ'],1178:['国語 │ 算数','理科 │ 社会'],1278:['春眠不覚暁','漢詩の一節'],1285:['山 川 木','日本語で使う漢字'],1390:['→ 〇 ＋ －','意味を示すしるし'],1398:['学校の新聞','運動会が開かれました'],1666:['春の あたたかな 風','言葉のまとまり'],1747:['中央区 │ 西区','区につけた名前'],1838:['1000 g ＝ 1 kg','重さの単位'],1899:['百の位  十の位  一の位','1       2       3'],1909:['五 │ 七 │ 五 │ 七 │ 七','最後の句'],2194:['読む │ 書く │ 話す','日本語を学ぶ教科'],2199:['峠   働','日本で作られた漢字'],2493:['あさ … 12ページ','いぬ … 24ページ'],2673:['2 ＋ 3 ＝ 5','数・形・量を学ぶ'],2930:['x ＋ 2 ＝ 5','数・図形・変化を調べる'],2931:['0 1 2 3 4','数を表す記号'],3178:['2 3 5 7 11','1 と自分自身だけで割れる'],3230:['犬 │ 私 │ 学校','名詞や代名詞'],3371:['犬 │ 学校','一つ一つの言葉'],3733:['私 は 本 を 読む。','「は」「を」が関係を示す'],3771:['80 点','テストの結果'],3817:['りんご という くだもの','名前を伝える'],3986:['学習の記録','授業 │ 活動 │ 成績'],4061:['やまだ はなこ','人につけた名前'],4090:['1  2  3','ナンバーで区別する'],4120:['10月13日  9時','日付 ＋ 時刻'],4142:['日本国憲法','国民主権 │ 人権 │ 平和'],4363:['はるのかぜ','くさばをゆらす','おとがする','五 ・ 七 ・ 五'],4585:['①  ②  ③','番号で区別する'],4926:['犬が走る。','まとまった意味のある文'],5161:['£ 1','イギリスなどのお金'],5168:['見本：実在しないカード','氏名 │ 写真 │ 住所'],5386:['1000 mA ＝ 1 A','電流の強さ'],5388:['1000 mL ＝ 1 L','体積の単位'],5439:['人 │ 犬 │ 学校','名前を表す言葉'],5529:['1 m ＝ 100 cm','長さの単位'],5532:['1 はじめに … 1ページ','2 お話 … 3ページ'],5763:['やま','山'],5859:['1 L ＝ 1000 mL','体積の単位'],5925:['がっこう','学校'],6024:['さくら','sakura'],6089:['本 を 読む。','動作の対象は「本」'],6090:['みかん','「ん」で終わると負け'],6242:['やまだ  はなこ','苗字      名前'],6281:['3 × 4 ＝ 12','1～9 のかけ算'],6306:['a b c','アルファベットの小文字'],6307:['A B C','アルファベットの大文字'],6315:['1学期 │ 2学期 │ 3学期','一年を分けた期間の例'],6374:['あさの ひかり','歌う言葉を作る'],6467:['0.5','1 を10等分したうちの5つ']}
NUMBERS={1541:9,2359:5,2644:3,2672:30,2766:7,2884:10,3836:10,4049:7,4093:2,4115:20,5998:6}
DAYS={51:1,1423:-1,1553:0,2482:-3,6121:2,6222:-2}
MONTHS={2654:3,2744:4,2767:7,2885:10,4101:2}
WEEK={1186:1,1627:4,2927:2,4121:6,5535:3,5742:None}
def build(item):
 i=item['id'];im=Image.new('RGB',(768,768),'#fffdf6');d=ImageDraw.Draw(im)
 d.rounded_rectangle((28,28,740,740),radius=35,outline='#d8e3e9',width=5)
 text(d,(384,88),item['word'],62)
 if i in NUMBERS:
  n=NUMBERS[i];text(d,(384,214),str(n),88,RED)
  for j in range(n):
   x=170+(j%10)*47 if n>10 else 180+(j%5)*90;y=350+(j//(10 if n>10 else 5))*86
   d.ellipse((x-15,y-15,x+15,y+15),fill=BLUE)
  text(d,(384,651),f'{n} こ',52)
 elif i==3113:
  for j in range(10):
   x=115+(j%5)*132;y=260+(j//5)*190
   d.rounded_rectangle((x-50,y-60,x+50,y+60),12,fill='#e3eef7',outline=BLUE,width=3);text(d,(x,y),'100',35)
  text(d,(384,647),'100 × 10 ＝ 1000',48,RED)
 elif i in DAYS:
  for j in range(-3,3):
   x=120+(j+3)*105;d.rounded_rectangle((x-45,285,x+45,410),10,fill='#ffdfba' if j==DAYS[i] else '#e8f1f5',outline=BLUE,width=3)
   text(d,(x,344),str(13+j),40)
  text(d,(435,467),'きょう 13日（例）',39)
  text(d,(384,614),f'{13+DAYS[i]}日',65,RED)
 elif i in MONTHS or i==2564:
  n=MONTHS.get(i,5)
  for j in range(1,13):
   x=145+(j-1)%4*159;y=255+(j-1)//4*125
   d.rounded_rectangle((x-58,y-43,x+58,y+43),10,fill='#ffdfba' if j==n else '#e8f1f5');text(d,(x,y),f'{j}月',37)
  text(d,(384,645),'陰暦の五月の別名' if i==2564 else f'一年の {n} 番目の月',39,RED)
 elif i in WEEK:
  for j,s in enumerate(['月','火','水','木','金','土','日']):
   x=105+j*93;d.rounded_rectangle((x-36,304,x+36,416),9,fill='#ffdfba' if WEEK[i]==j else '#e8f1f5');text(d,(x,360),s,47)
  text(d,(384,575),'一週間の曜日',48)
 elif i in [2625,2626,6223]:
  labels=['今月','来月','再来月'] if i==2625 else (['一昨年','去年','今年'] if i==6223 else ['今年','来年','再来年'])
  for j,s in enumerate(labels):
   x=155+j*230;d.rounded_rectangle((x-95,290,x+95,430),12,fill='#ffdfba' if j==(0 if i==6223 else 2) else '#e8f1f5');text(d,(x,360),s,42)
  arrow(d,(135,535),(635,535));text(d,(384,633),'時間が進む方向',37)
 elif i in [3552,3838,1335,2321]:
  text(d,(384,208),'1月' if i==1335 else 'ある月の例',45)
  for j in range(1,32):
   x=120+(j-1)%7*87;y=286+(j-1)//7*75
   d.rounded_rectangle((x-33,y-29,x+33,y+29),5,fill='#ffdfba' if j==(10 if i==3838 else 1) else '#e8f1f5');text(d,(x,y),str(j),29)
 elif i in [1406,4092,4109,5304,5347]:
  cx=384;cy=390;line(d,(cx,240),(cx,540));line(d,(210,cy),(558,cy))
  for xy,s in [((384,209),'北'),((384,580),'南'),((605,390),'東'),((163,390),'西')]:text(d,xy,s,55,RED if s==item['word'] else BLUE)
  if i==5304:arrow(d,(384,390),(550,390));text(d,(384,663),'北を向くと、右は東',38)
 elif i in [3128,3129,5387]:
  line(d,(120,385),(650,385))
  for j in range(11):line(d,(120+j*53,385),(120+j*53,335 if j in [0,10] else 360),width=4)
  text(d,(120,438),'0',40);text(d,(650,438),'1 cm',40)
  arrow(d,(120,525),(650 if i!=5387 else 173,525));text(d,(384,643),'1 cm ＝ 10 mm',45)
 elif i in [332,1034]:
  text(d,(384,270),'朝 → 昼 → 夜' if i==332 else '新月 → 半月 → 満月 → 新月',42 if i==332 else 36)
  if i==332:
   for j in range(3):d.ellipse((115+j*224,350,205+j*224,440),fill=['#ffd879','#f3c946','#416590'][j])
  else:
   for j,color in enumerate(['#416590','#416590','#ffd879','#416590']):d.ellipse((95+j*170,350,185+j*170,440),fill=color)
   d.pieslice((265,350,355,440),-90,90,fill='#ffd879')
  text(d,(384,599),'ひとつの日' if i==332 else '月の満ち欠けの一周',44)
 elif i==4138:
  for j,n in enumerate([3,6]):
   for k in range(n):d.ellipse((100+k*95,310+j*180,140+k*95,350+j*180),fill=BLUE)
  text(d,(384,635),'3 の二つ分は 6',44,RED)
 elif i in [5522,4637,6467]:
  n=10 if i in [4637,6467] else 4
  for y in range(n):
   for x in range(n):
    left=174+x*420/n;top=230+y*340/n
    d.rectangle((left,top,left+420/n,top+340/n),fill=('#f8ba75' if i in [4637,6467] and y<5 else '#d6e8f3'),outline=BLUE,width=2)
  text(d,(384,641),'100ますのうち50ます＝50%' if i==4637 else ('半分 ＝ 0.5' if i==6467 else '1ますずつ、広さを数える'),39)
 elif i==4757:
  for j in range(25):
   x=200+j%5*90;y=265+j//5*73;d.rectangle((x-35,y-28,x+35,y+28),fill='#ffdca6' if j//5==2 else '#e8f1f5',outline=BLUE,width=2);text(d,(x,y),str(j+1),28)
  text(d,(384,660),'一列そろった！',43,RED)
 elif i in [3931,6192,6419]:
  if i==3931:
   d.rounded_rectangle((347,250,403,539),20,outline=BLUE,width=6);d.ellipse((331,507,419,595),fill=RED);line(d,(375,330),(375,552),RED,14)
   text(d,(570,320),'100 ℃',44);text(d,(570,535),'0 ℃',44)
  else:
   text(d,(384,220),'日本（北半球）',42);d.rectangle((100,340,665,405),fill='#385b8d');d.rectangle((100,340,100+(220 if i==6192 else 420),405),fill='#ffd464');text(d,(384,478),'昼（日の出～日の入り）',38);text(d,(384,604),'最も短いころ' if i==6192 else '最も長いころ',44,RED)
 elif i in [6460,6462]:
  a=(210,535);b=(610,535);c=(210,230) if i==6462 else (410,535-200*math.sqrt(3));line(d,a,b);line(d,a,c)
  if i==6462:d.line([(210,490),(255,490),(255,535)],fill=RED,width=5)
  else:d.arc((110,435,310,635),-60,0,fill=RED,width=6)
  text(d,(440,375),'90°' if i==6462 else '60°',64,RED)
 elif i in [6463,6464]:
  d.ellipse((174,200,594,620),outline=BLUE,width=7);d.ellipse((377,403,391,417),fill=BLUE)
  line(d,(174 if i==6463 else 384,410),(594,410),RED,9);text(d,(384,677),'円の中心を通る' if i==6463 else '中心から、ふちまで',39)
 elif i==6441:
  d.polygon([(120,510),(360,240),(650,510)],fill='#d8e6d6');line(d,(100,540),(650,540),'#3687bf');arrow(d,(560,538),(560,240));text(d,(350,600),'平均的な海面：0 m',40);text(d,(560,180),'高さ',40)
 elif i==6187:
  d.ellipse((180,210,588,618),outline=BLUE,width=6)
  for w in [60,140,204]:d.ellipse((384-w,210,384+w,618),outline=BLUE,width=3)
  line(d,(384,210),(384,618),RED,7);text(d,(384,665),'基準の経線：0°',42)
 elif i==6337:
  for y in range(5):
   for x in range(6):d.rectangle((180+x*70,230+y*70,250+x*70,300+y*70),outline=BLUE,width=3)
  for j,s in enumerate('さくら'):text(d,(215+j*70,265),s,48)
 elif i==6212:
  # Schematic external field: every arrow travels from the red N face to blue S.
  for side in [-1,1]:
   for j in range(3):
    pts=[(260,400+side*(10+j*10)),(65-j*25,400+side*(150+j*55)),(705+j*25,400+side*(150+j*55)),(510,400+side*(10+j*10))]
    def point(t):return tuple((1-t)**3*pts[0][k]+3*(1-t)**2*t*pts[1][k]+3*(1-t)*t*t*pts[2][k]+t**3*pts[3][k] for k in [0,1])
    path=[point(k/200) for k in range(201)];d.line(path,fill=BLUE,width=5)
    arrow(d,point(.47),point(.53),BLUE)
  d.rectangle((260,350,384,450),fill=RED);d.rectangle((384,350,510,450),fill=BLUE)
  text(d,(320,400),'N',57,'white');text(d,(448,400),'S',57,'white')
  text(d,(384,674),'磁石の外側：N極 → S極',39)
 elif i in EXAMPLES:
  lines=EXAMPLES[i]
  d.rounded_rectangle((65,190,703,657),radius=24,fill='#edf5f8',outline='#b9cfdf',width=4)
  for j,s in enumerate(lines):text(d,(384,290+j*115),s,64 if len(s)<10 else 45,RED if j==0 else BLUE)
 else:raise ValueError('Missing exact diagram implementation: '+str(i))
 return im.resize((256,256),Image.Resampling.LANCZOS)
def main():
 plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'));items=[x for x in plan if not x['sheet']]
 output=[]
 for x in items:
  target=ROOT/'assets/shiritori'/x['filename'];source=ROOT/'assets/shiritori'/x['sourceSheet']
  picture=build(x)
  for dest in [target,source]:
   if dest.exists():
    with Image.open(dest) as existing:
     if existing.convert('RGB').tobytes()!=picture.tobytes():raise ValueError('Refusing to overwrite differing diagram '+str(dest))
   else:picture.save(dest,optimize=True)
  output.append(dict(id=x['id'],file=x['filename'],sha256=hashlib.sha256(target.read_bytes()).hexdigest(),scene=x['scene'],generator='scripts/build-shiritori-wave10-diagrams.py'))
 (BASE/'diagram-validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('Created',len(output),'exact diagrams')
if __name__=='__main__':main()
