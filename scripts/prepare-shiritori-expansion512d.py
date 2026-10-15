"""Freeze an independent, rights-conscious intake. Never mutate live data here."""
import csv, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-15-expansion512d'
OUT=ROOT/'data/dictionary-imports'
WORK=ROOT/'data/image-coverage'/NAME
WORK.mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
KANA_TABLE=str.maketrans({chr(i):chr(i-96) for i in range(0x30a1,0x30f7)})
def norm(s):return unicodedata.normalize('NFKC',s).casefold().replace('・','').replace(' ','').translate(KANA_TABLE)
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
blocked={r['reading'] for r in live}
reserved=set()
for p in OUT.glob('*'):
 if NAME in p.name or not p.is_file():continue
 if p.suffix=='.csv':
  try:reserved.update(r.get('reading','') for r in csv.DictReader(p.open(encoding='utf-8-sig')))
  except (UnicodeError,csv.Error):pass
 elif p.suffix=='.txt':
  for line in p.read_text(encoding='utf-8').splitlines():
   for token in line.split('|'):
    m=re.match(r'^([ぁ-ゖー]+)(?:[ |]|$)',token.strip())
    if m:reserved.add(m[1])
for p in (ROOT/'data/image-coverage').glob('*/draft.json'):
 if NAME in str(p):continue
 data=json.loads(p.read_text(encoding='utf-8'))
 reserved.update(x['reading'] for x in data.get('items',[]))
rules=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)',line,re.I)
 rules.append((m[1].lower(),norm(m[2].strip())) if m else ('contains',norm(line)))
items=[];excluded=[];seen=set();words={norm(r['word']) for r in live}
for line in (OUT/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
 if not line or line.startswith('#'):continue
 if line.startswith('['):group=line[1:-1];continue
 fields=line.split('|');reading,word=fields[:2]
 reason=('existing-reading' if reading in blocked else 'reserved-other-batch' if reading in reserved else 'duplicate-candidate' if reading in seen else 'existing-spelling' if norm(word) in words else None)
 if not re.fullmatch('[ぁ-ゖー]+',reading):reason='invalid-reading'
 if any(reading==p if m=='exact' else p in reading for m,p in rules):reason='blacklist'
 if reason:excluded.append(dict(reading=reading,word=word,reason=reason));continue
 seen.add(reading);words.add(norm(word))
 meaning=fields[2] if len(fields)>2 else (f'{group.split(":")[1]}の競技で知られるスポーツ選手。' if group.startswith('選手:') else {'野球チーム':'日本のプロ野球チームの名前。','サッカーチーム':'日本のサッカークラブの名前。','バスケチーム':'日本のバスケットボールクラブの名前。'}[group])
 assert not any(c in meaning for c in ',\n\r')
 items.append(dict(reading=reading,word=word,meaning=meaning,category=group,level=2 if group in ['料理','飲み物'] else 3))
# Mere elongated spelling variants do not count as another word.
items=[x for x in items if x['reading'] not in {'しゃくしゅーか','くっぱじゅにあー','なーん','こんすけ','はっさん'}]
save(WORK/'candidates.json',items)
save(WORK/'exclusions.json',excluded)
save(WORK/'reservation-snapshot.json',dict(readings=sorted(reserved),liveRows=len(live),liveSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest()))
print(json.dumps(dict(eligible=len(items),categories=Counter(x['category'] for x in items),excluded=Counter(x['reason'] for x in excluded)),ensure_ascii=False))

def balanced(pool,n):
 assert len(pool)>=n,(len(pool),n)
 groups={}
 for x in pool:groups.setdefault(x['category'],[]).append(x)
 result=[]
 while len(result)<n:
  for group in groups.values():
   if group and len(result)<n:result.append(group.pop(0))
 return result
joc=json.loads(Path('C:/Users/user/.cache/shiritori-qa/expansion512d-sources/joc.txt').read_text(encoding='utf-8-sig'))
canon=lambda s:norm(s).translate(str.maketrans('髙邊','高辺'))
for x in items:
 if x['category'].startswith('選手:'):
  matches=[r for r in joc if canon(r['familynameja']+r['fisrtnameja'])==canon(x['word'])]
  if matches:
   r=matches[0]
   if x['reading']!=norm(r['familynamekana']+r['fisrtnamekana']):print('OFFICIAL READING',x['word'],x['reading'],norm(r['familynamekana']+r['fisrtnamekana']));x['reading']=norm(r['familynamekana']+r['fisrtnamekana'])
   x.update(sources=['https://www.joc.or.jp'+r['profilelink']],sourceRecord={k:r[k] for k in ['label','familynamekana','fisrtnamekana','sports']},lexicalSource='JOC公式選手データ（2026-10-15照合）')
  elif x['reading']=='おおたにしょうへい':x.update(sources=['https://www.mlb.com/ja/player/shohei-ohtani-660271'],lexicalSource='MLB公式選手プロフィール')
items=[x for x in items if not x['category'].startswith('選手:') or x.get('sources')]
selected=[]
for prefix,count in [('料理',128),('飲み物',32),('選手:',96),('チーム',96),('ゲーム',80),('キャラクター',80)]:
 pool=[x for x in items if (x['category'].startswith(prefix) if prefix=='選手:' else prefix in x['category'] if prefix in ['チーム','キャラクター'] else x['category']==prefix)]
 selected+=balanced(pool,count)
assert len(selected)==len({x['reading'] for x in selected})==512
for n,x in enumerate(selected):x.update(slot=n+1,filename=f'expansion512d-card-{n+1:03}.png' if n>=160 else f'expansion512d-food-{n+1:03}.png',assignment='new',credit='AI生成イラスト' if n<160 else '独自文字カード（外部検索なし）')
for n in range(10):
 group=selected[n*16:(n+1)*16]
 prompt='Edit the attached equal 4 by 4 grid template. Preserve its 2048x2048 dimensions, all five vertical and five horizontal continuous pure magenta #ff00ff lines including outer border, equal cell geometry and line widths. Draw one separate accurate recognizable warm watercolor food illustration in each white cell, row-major order. No text, letters, numbers, labels, logos, product packaging, people or characters. No magenta in the artwork. Keep every dish and its shadow in its own cell. Use the cell generously; no forced white-margin ratio. Food is plated or served in plain unbranded vessels. Show the following 16 DIFFERENT foods accurately:\n'
 for i,x in enumerate(group,1):prompt+=f'{i}. {x["word"]}: {x["meaning"]}\n';x.update(sheet=n+1,tileIndex=i,sourceSheet=f'sheets/expansion512d-sheet{n+1:02}.png',cropValidation=f'data/image-coverage/{NAME}/sheet{n+1:02}-crop.json',scene=x['word']+'：'+x['meaning'])
 (WORK/f'sheet{n+1:02}.prompt.txt').write_text(prompt,encoding='utf-8')
save(WORK/'plan.json',dict(name=NAME,baselineRows=len(live),items=selected,illustrations=160,cards=352,sheets=10))
