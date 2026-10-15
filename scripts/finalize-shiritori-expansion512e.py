"""Freeze 512 non-overlapping words, draw name cards, and append with history."""
import argparse,csv,hashlib,io,json,subprocess,sys,unicodedata
from collections import Counter
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];NAME='2026-10-15-expansion512e'
OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
CARD='独自文字カード（外部検索なし）'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def run(*a):subprocess.run(a,cwd=ROOT,check=True)
def norm(s):return unicodedata.normalize('NFKC',s).replace('・','').replace(' ','').casefold()
ap=argparse.ArgumentParser();ap.add_argument('--import-all',action='store_true');args=ap.parse_args()
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
if not args.import_all and (OUT/'plan.json').exists():
 frozen=read(OUT/'plan.json');pairs={(x['reading'],x['word']) for x in live}
 if len(frozen.get('items',[]))==512 and all((x['reading'],x['word']) in pairs for x in frozen['items']):
  print('Already imported: preserve the frozen plan and use the music finalizer or tests.');sys.exit()
if not args.import_all:
 pool=read(OUT/'candidates.json');snapshot=read(OUT/'reservation-snapshot.json')
 # A source dictionary's alternative spellings do not make new vocabulary.
 dictionary=read(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json'))
 oldsurfaces={norm(r['word']) for r in live};oldentries=set()
 for e in dictionary['words']:
  if any(norm(f['text']) in oldsurfaces for f in e['kanji']+e['kana']):oldentries.add(e['id'])
 aliases=[];eligible=[];entryseen=set()
 for x in pool:
  reason=x.get('omit')
  if x['category'] in ['楽器','音楽ジャンル'] and x.get('entryId'):
   if x['entryId'] in oldentries:reason='existing-dictionary-spelling-alias'
   if x['entryId'] in entryseen:reason='same-dictionary-entry-alias'
   entryseen.add(x['entryId'])
  if reason:aliases.append(dict(word=x['word'],reading=x['reading'],reason=reason));continue
  eligible.append(x)
 # Put the best known characters from every story arc before minor participants.
 priority='ゴン キルア クラピカ レオリオ ヒソカ カイト クロロ マチ シズク シャルナーク ノブナガ パクノダ フランクリン フィンクス ウボォーギン フェイタン ボノレノフ ネテロ イルミ ゼノ シルバ キキョウ ミルキ カナリア ゴトー ビスケ ゲンスルー ゴレイヌ レイザー アベンガネ ツェズゲラ コムギ ネフェルピトー シャウアプフ モントゥトゥユピー コルト メレオロン イカルゴ ウェルフィン ザザン ヂートゥ レオル ヒリン フラッタ ラモット モラウ ノヴ パーム＝シベリア ナックル＝バイン シュート センリツ ゼパイル サトツ ハンゾー トンパ ポックル ウイング'.split()
 def rank(x):return priority.index(x['word']) if x['word'] in priority else len(priority)
 quotas={'楽器':80,'音楽ジャンル':72,'漫画':64,'ドラゴンボール':64,'モビルスーツ':56,'サンリオ':64,'HUNTER×HUNTER':80,'北斗の拳':32}
 selected=[]
 for category,count in quotas.items():
  group=[x for x in eligible if x['category']==category]
  if category=='HUNTER×HUNTER':group.sort(key=rank)
  assert len(group)>=count,(category,len(group),count)
  selected+=group[:count]
 assert len(selected)==len({x['reading'] for x in selected})==512
 for n,x in enumerate(selected,1):
  x.update(slot=n,imageStatus='search-only' if x['category'] in ['楽器','音楽ジャンル'] else 'name-card',imageReason='楽器や音楽の検索画像は既存のライセンス確認付き検索を利用。保存画像は今回作成しない。' if x['category'] in ['楽器','音楽ジャンル'] else '文字と読みだけの独自カード。人物・キャラクター・機体の絵や公式ロゴは使用せず、外部画像検索を行わない。')
  evidence=x.get('sourceEvidence')
  if isinstance(evidence,list):
   allowed={'楽器':set(),'音楽ジャンル':set(),'漫画':{'jump.html'},'ドラゴンボール':{'dragon.html','dragon-super.html','dragon-z.html'},'モビルスーツ':{'seed.html','seed-destiny.html','gwitch.html','gqux.html'}}.get(x['category'],set())
   evidence=[v for v in evidence if v in allowed];x['sourceEvidence']=evidence
  if x.get('entryId'):
   x.update(evidenceType='dictionary-headword',lexicalSource='JMdict '+str(x['entryId'])+' / '+dictionary['dictDate'])
  elif evidence:
   x.update(evidenceType='primary-name-list' if isinstance(evidence,dict) else 'primary-name-mention',lexicalSource='公式資料の名称を照合。読みと短い説明は独自に編集確認。文字列の掲載確認と紹介内容の個別検証は区別。')
  else:
   x.update(evidenceType='editorial-name-or-style',lexicalSource='作品・楽器・音楽様式の一般的な名称として編集確認。参照URLの全名称個別掲載を確認したとの主張ではない。')
  x.update(meaningReason='今回の意味を限定した独自説明：'+x['meaning'],ageReason='専門的な固有名・音楽用語のため上級。作品の視聴や購読の年齢適合性の推薦とは区別し、説明は刺激の強い描写を避けた。')
  if x['imageStatus']=='name-card':
   x.update(filename=f'expansion512e-card-{n:03}.png',sourceSheet=f'sheets/expansion512e-diagram-{n:03}.png',credit=CARD)
 save(OUT/'plan.json',dict(name=NAME,items=selected,categories=quotas,reservationSnapshot='reservation-snapshot.json',date='2026-10-16'))
 save(OUT/'alias-exclusions.json',aliases)
 # Cards are code-native typography. No generated or borrowed character art.
 font='C:/Windows/Fonts/BIZ-UDGothicR.ttc';layouts=[]
 def lines_for(d,text,top,height,start,color):
  for size in range(start,21,-1):
   f=ImageFont.truetype(font,size);lines=[];line=''
   for c in text:
    if d.textlength(line+c,font=f)>650:lines.append(line);line=''
    line+=c
   if line:lines.append(line)
   if len(lines)*(size+14)<=height:break
  assert len(lines)*(size+14)<=height,text
  for i,line in enumerate(lines):d.text((384,top+i*(size+14)),line,anchor='mt',font=f,fill=color)
  return dict(lines=lines,size=size)
 for x in selected:
  if x['imageStatus']!='name-card':continue
  im=Image.new('RGB',(768,768),'#101c2b');d=ImageDraw.Draw(im)
  d.rounded_rectangle((26,26,742,742),24,outline='#72bca4',width=4)
  d.text((384,66),x['category'],anchor='mt',font=ImageFont.truetype(font,30),fill='#b6c7d3')
  title=lines_for(d,x['word'],173,260,52,'#eff9ff');rd=lines_for(d,x['reading'],470,190,38,'#9bedd0')
  d.text((384,696),'なまえを よんでみよう',anchor='mt',font=ImageFont.truetype(font,26),fill='#b6c7d3')
  im.save(ROOT/'assets/shiritori'/x['sourceSheet'])
  im.resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'assets/shiritori'/x['filename'])
  layouts.append(dict(slot=x['slot'],title=title,reading=rd,sha256=hashlib.sha256((ROOT/'assets/shiritori'/x['filename']).read_bytes()).hexdigest()))
 save(OUT/'card-layouts.json',layouts)
 save(DATA/(NAME+'.review.json'),selected)
 save(DATA/(NAME+'.source.json'),dict(date='2026-10-16',policy='名称と出典の事実記録。説明は独自作成。公式のイラスト・文章は転載しない。辞書由来の部分はCC BY-SA 4.0。個別掲載を未確認の編集語を区別。',dictionaryDate=dictionary['dictDate'],dictionaryAttribution='James William BREEN / EDRDG',dictionaryLicense='https://www.edrdg.org/edrdg/licence.html',rows=[{k:x[k] for k in ['slot','reading','word','sources','evidenceType','sourceEvidence','dictionaryEvidence'] if k in x} for x in selected]))
 print(json.dumps(dict(prepared=512,categories=quotas,cards=len(layouts),searchOnly=512-len(layouts),aliasExclusions=len(aliases)),ensure_ascii=False));sys.exit()

plan=read(OUT/'plan.json');items=plan['items']
before=(ROOT/'whitelist.csv').read_text(encoding='utf-8');live=list(csv.DictReader(io.StringIO(before)))
if all(any(r['reading']==x['reading'] and r['word']==x['word'] for r in live) for x in items):print('Already imported; run validation.');sys.exit()
# The previous active batch assigned its IDs before this work. Wait until those
# rows exist, instead of displacing its reserved row IDs.
previous=ROOT/'data/image-coverage/2026-10-15-expansion512d/plan.json'
if previous.exists():
 prior=read(previous)
 assert all(any(r['reading']==x['reading'] and r['word']==x['word'] for r in live) for x in prior['items']),'Preceding expansion512d is still importing; keep this prepared intake separate.'
old={r['reading'] for r in live};oldwords={norm(r['word']) for r in live}
assert not [x['word'] for x in items if x['reading'] in old or norm(x['word']) in oldwords],'Live dictionary collision; refresh selection before import.'
assert read(DATA/'history.json')[-1]['afterSha256']==sha(before)
for n,x in enumerate(items,1):x['id']=len(live)+n
plan.update(baselineRows=len(live),baselineSha256=sha(before));save(OUT/'plan.json',plan);save(DATA/(NAME+'.review.json'),items)
batch=DATA/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
 for x in items:w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only')
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
imagebatch=ROOT/'data/batches'/(NAME+'-cards.csv')
columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','credit','prompt']
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in items:
  if x['imageStatus']=='name-card':w.writerow({**{k:x[k] for k in ['id','reading','word','meaning','filename','sourceSheet','credit']},'scene':x['imageReason'],'tileIndex':1,'generatedAt':'2026-10-16','prompt':'Code-native typography only: '+x['word']+' / '+x['reading']})
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
after=(ROOT/'whitelist.csv').read_text(encoding='utf-8');assert after.startswith(before)
rows=list(csv.DictReader(io.StringIO(after)));coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');assert len(coverage)==len(live)
for x in items:
 r=rows[x['id']-1]
 coverage.append(dict(id=x['id'],**{k:r[k] for k in ['reading','word','meaning','level','image_asset']},category=x['category'],target=x['imageStatus']=='name-card',scopeReason=x['imageReason'],status='covered' if x['imageStatus']=='name-card' else 'search-only',assignment='new' if x['imageStatus']=='name-card' else 'none'))
save(ROOT/'data/image-coverage/review-2026-10-10.json',coverage)
summary=dict(date='2026-10-16',addedWords=512,newReadings=512,baselineRows=len(live),totalRows=len(rows),categories=dict(Counter(x['category'] for x in items)),nameCards=sum(x['imageStatus']=='name-card' for x in items),searchOnly=sum(x['imageStatus']=='search-only' for x in items),endingN=sum(x['reading'].endswith('ん') for x in items),beforeSha256=sha(before),afterSha256=sha(after))
save(OUT/'summary.json',summary);save(DATA/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
