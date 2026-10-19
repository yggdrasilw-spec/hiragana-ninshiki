"""Prepare a separate, resumable vocabulary/image intake; never edit the live dictionary."""
import csv,json,re,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1]; O=R/'data/image-coverage/2026-10-19-nature512';O.mkdir(exist_ok=True)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
base=(R/'whitelist.csv').read_bytes();rows=list(csv.DictReader(base.decode().splitlines()))
reserved=[]
for p in (R/'data/image-coverage').glob('2026-10-19-*/plan.json'):
 if p.parent!=O:
  reserved+=json.loads(p.read_text(encoding='utf-8')).get('items',[])
known={x['reading'] for x in rows+reserved};words={x['word'] for x in rows+reserved}
items=[];excluded=[];category=''
sources={
 'elements':'https://iupac.org/what-we-do/periodic-table-of-elements/',
 'angels':'https://www.sacred-texts.com/bib/boe/boe023.htm',
 'demons':'https://www.sacred-texts.com/grim/lks/index.htm',
 'accessories':'https://store.metmuseum.org/blog/the-met-store-jewelry-glossary',
 'minerals':'https://www.nhm.ac.uk/our-science/services/collections/mineralogy/minerals.html',
 'gems':'https://www.gia.edu/jp/gem-encyclopedia',
 'frogs':'https://amphibiaweb.org/lists/Dendrobatidae.shtml',
 'reptiles':'https://reptile-database.reptarium.cz/',
 'danger':'https://animaldiversity.org/',
 'toxic':'https://www.nies.go.jp/biodiversity/invasive/'}
elements=[]
for z,line in enumerate((O/'elements.txt').read_text(encoding='utf-8').splitlines(),1):
 reading,word,symbol,en,detail,scene=line.split('|')
 elements.append(dict(reading=reading,word=word,symbol=symbol,atomicNumber=z,english=en,meaning=f'原子番号{z}、元素記号{symbol}の元素。'+detail,scene=scene))
assert len(elements)==118
save(O/'elements.json',elements)
for e in elements:
 if e['reading'] in known or e['word'] in words:
  excluded.append(dict(reading=e['reading'],word=e['word'],reason='既存元素。記号・番号の補完対象として別に保存。'));continue
 items.append(dict(e,category='elements',grade=4,level=3,scientificName='',lexicalSource=dict(url=sources['elements'],atomicNumber=e['atomicNumber'],symbol=e['symbol']),meaningReason='原子番号・元素記号と日本語名を対応。',ageReason='専門的な化学の名称としてレベル4。',imageReason='元素そのもの・用途・研究装置の説明イメージ。超重元素の巨視的な塊は描かない。'))
 known.add(e['reading']);words.add(e['word'])
for line in (O/'candidates.txt').read_text(encoding='utf-8').splitlines():
 if line.startswith('@'):category=line[1:];continue
 if not line or line.startswith('#'):continue
 a=line.split('|');reading,word,detail=a[:3]
 if reading in known or word in words:
  excluded.append(dict(reading=reading,word=word,reason='既存辞書または同日進行中バッチに登録・予約済み'));continue
 assert re.fullmatch('[ぁ-ゖー]+',reading),reading
 assert ',' not in detail and len(a)>=4,line
 scientific=a[3] if category in ['reptiles','frogs','danger','toxic'] else ''
 scene=a[4] if scientific else a[3]
 grade=4
 if category in ['angels','demons']:grade=5
 if category=='accessories':grade=3
 meaning=detail
 if scientific:meaning+=' 学名：'+scientific+'。'
 primary=sources[category]
 if category=='reptiles':primary='https://reptile-database.reptarium.cz/species?genus='+scientific.split()[0]+'&species='+scientific.split()[1]
 x=dict(reading=reading,word=word,meaning=meaning,category=category,scientificName=scientific,scene=scene,grade=grade,level=min(grade,3),lexicalSource=dict(url=primary,lookupWord=word,scientificName=scientific),meaningReason='対象・種または亜種・素材または名称を区別した日本語説明。'+detail,ageReason='分野別の名称として編集判断。'+('宗教・伝承の固有名なのでレベル5。' if grade==5 else '専門名はレベル4。' if grade==4 else '身につける装飾品として高学年向けレベル3。'),imageReason='語義と識別特徴を照合する教育用イラスト。'+scene)
 items.append(x);known.add(reading);words.add(word)
save(O/'pool.json',items);save(O/'excluded.json',excluded)
print(json.dumps(dict(pool=len(items),categories=dict(collections.Counter(x['category'] for x in items)),excluded=len(excluded)),ensure_ascii=False))
if __name__=='__main__':
 reject={'おかぴやどくがえる','とーりえやどくがえる','ぬまーたすやどくがえる','よーぐるとひるやもり','うぇべるやもり','もりどらごんもどき','もんはなけん','かりえん','ほうようこう','ぎんぐろ','ぶらっくぷれーととかげ','まだけすかるぼあ','せいろんにしきへび','きたまつかさとかげ','いりあんじゃやあおじたとかげ','けいあおじたとかげ','みりーがえる','はなながどろがめ','のどじろどろがめ','にしあふりかはこよこくびがめ','よこくびがめ','しんりんおおかみ','ひらりーかえるがめ','じーべんろっくながくびがめ','ちりめんながくびがめ','きぼしぬまはこがめ','ひげこちはりとかげ','ほるもさんとっくろへび','はなおこぜ','ひれながはぎ','たまやすで','いもがい','きろねっくすふれっけり','おおむかで','しゅもくざめ','ぴぐみーまるがおおとかげ','でれあんたまおやもり','けーんたまおやもり','だいおういしやもり','びーどろやもり','くろはらへびくびがめ','ふせんせおれがめ','かんばーらんどきみみがめ','りおぐらんであかみみがめ','よーろっぱあしなしかげ','にしあしなしかげ','はなながくびがめ','はなながどろがめ','きんこうせき'}
 fixes={'くばんわに':('きゅーばわに','キューバワニ'),'できさすさんごへび':('てきさすさんごへび','テキサスサンゴヘビ'),'きんこうせき':('きんこうせき','金紅石')}
 pools=collections.defaultdict(list);taxa=set()
 for x in items:
  if x['reading'] in reject or '未確認' in x['meaning'] or 'Candidate to exclude' in x['scene']:continue
  if x['reading'] in fixes:x['reading'],x['word']=fixes[x['reading']]
  if x['category'] in ['reptiles','frogs']:
   if x['scientificName'] in taxa:continue
   taxa.add(x['scientificName'])
  pools[x['category']].append(x)
 print('usable',dict((k,len(v)) for k,v in pools.items()))
 quotas=dict(elements=103,angels=8,demons=24,accessories=40,gems=48,minerals=72,frogs=24,reptiles=120,danger=32,toxic=41)
 # Fill any genuine shortfall with reviewed minerals/gems, never invented species.
 selected=[]
 for cat,n in quotas.items():
  group=pools[cat]
  if cat=='reptiles':
   snakes=[x for x in group if any(w in x['scientificName'] for w in ['Python','Morelia','Antaresia']) or any(w in x['word'] for w in ['ヘビ','ナメラ','スネーク','ボア','パイソン','ウォーマ','シュウダ'])]
   turtles=[x for x in group if any(w in x['word'] for w in ['ガメ','リクガメ'])]
   lizards=[x for x in group if x not in snakes+turtles]
   # Keep breadth across all three families; overflow retains source order.
   group=snakes[:40]+lizards[:40]+turtles[:40]+snakes[40:]+lizards[40:]+turtles[40:]
  selected+=group[:n]
 for cat in ['minerals','gems','accessories','demons','reptiles','danger','toxic','frogs']:
  for x in pools[cat]:
   if len(selected)>=512:break
   if x not in selected:selected.append(x)
 assert len(selected)==512,len(selected)
 assert len({x['reading'] for x in selected})==512
 if (O/'plan.json').exists():raise SystemExit('Frozen plan already exists; no overwrite')
 for slot,x in enumerate(selected):
  x.update(slot=slot+1,sheet=slot//16+1,tileIndex=slot%16+1,filename=f'nature512-slot-{slot+1:03}.png')
 prefix='Edit this 2048x2048 equal 4 by 4 template. Fill exactly sixteen white cells with separate clear educational watercolor illustrations in row-major order. Preserve all FIVE horizontal and FIVE vertical continuous pure MAGENTA #ff00ff lines including outer frame at exactly their positions and width. No artwork crosses a line. Magenta reserved only for grid. No text, no letters, no numbers, no labels, no watermarks. Keep entire subjects and shadows in their cells; use cell space generously. Correct anatomy and specimen shapes. No harm, attacks, handling dangerous animals, or recognizable modern fictional character designs. Each element image is a conceptual explanation of substance/use/research, not an atom photograph. Exact order:\n'
 sheets=[]
 for s in range(1,33):
  tiles=[x for x in selected if x['sheet']==s]
  prompt=prefix+'\n'.join(f'{i+1}. {x["word"]}: {x["scene"]}.' for i,x in enumerate(tiles))
  (O/f'sheet{s:02}.prompt.txt').write_text(prompt,encoding='utf-8');sheets.append(dict(sheet=s,tiles=tiles,prompt=prompt))
 (O/'registration-baseline.csv').write_bytes(base)
 save(O/'plan.json',dict(batch=O.name,status='planned',baselineRows=len(rows),baselineSha256=hashlib.sha256(base).hexdigest(),items=selected,sheets=sheets,existingElementReadings=[e['reading'] for e in elements if e['reading'] in {r['reading'] for r in rows}]))
 save(O/'sources.json',sources)
 print('selected',dict(collections.Counter(x['category'] for x in selected)))
