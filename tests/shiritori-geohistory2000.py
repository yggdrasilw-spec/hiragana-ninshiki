"""Verify the complete new intake, source linkage and preserved prior dictionary."""
import csv,json,hashlib,collections,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-28-geohistory2000'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));sources=read(BASE.with_suffix('.sources.json'))
raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
assert s['registered'] and len(items)==2000 and len(rows)>=s['baselineRows']+2000
intake=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+2001])+b'\n'
assert hashlib.sha256(intake).hexdigest()==s['afterSha256'],'Imported prefix must match; subsequent recorded appends are allowed'
baseline=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n'
assert hashlib.sha256(baseline).hexdigest()==s['beforeSha256'],'Prior 17707 rows must remain byte-for-byte'
keys=lambda xs:{(x['reading'],x['word'],x['meaning']) for x in xs}
assert len(keys(items))==2000 and not keys(items)&keys(rows[:s['baselineRows']])
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json');grades=read(ROOT/'data/shiritori-grade-review.json')
assert len(coverage)==len(updates['entries'])==len(grades)==len(rows)
assert updates['csvSha256']==hashlib.sha256(raw).hexdigest()
for x in items:
 r=rows[x['id']-1];assert all(str(x[k])==r[k] for k in r),(x['id'],x['word'])
 assert re.fullmatch('[ぁ-ゖー]+',r['reading']) and r['image_mode']=='none' and not r['image_asset']
 assert grades[x['id']-1]['level']==5 and grades[x['id']-1]['meaning']==x['meaning']
 assert coverage[x['id']-1]['status']=='explanation-only' and coverage[x['id']-1]['meaning']==x['meaning']
 assert updates['entries'][x['id']-1]['text']==[x['reading'],x['word'],x['meaning']]
 assert x['lexicalSource'] and x['meaningReason'] and x['ageReason']
 if any(y['reading']==x['reading'] for y in rows[:s['baselineRows']]):assert x.get('distinctSenseReason')
assert len([x for x in items if x['category']=='アメリカの州'])==50
assert len([x for x in items if x['category']=='アメリカの州都'])==50
assert len({x['state'] for x in items if x['category']=='アメリカの州'})==50
facts={x['geonameId']:x for x in sources['geoNamesSelected']}
for x in items:
 if x.get('geonameId'):
  fact=facts[x['geonameId']]
  assert fact['word']==x['word'] and fact['countryCode']==x['countryCode'] and fact['featureCode'] in ['PPL','PPLA','PPLA2']
assert len(facts)==len([x for x in items if x.get('geonameId')])
assert all(x['matched'] or x.get('editorialResolution') for x in sources['readingChecks'])
checks={'魏':'ぎ','呉':'ご','蜀':'しょく','御成敗式目':'ごせいばいしきもく','班田収授の法':'はんでんしゅうじゅのほう','ネブカドネザル2世':'ねぶかどねざるにせい','三国志':'さんごくし','西ローマ帝国':'にしろーまていこく','大連':'だいれん','石橋湛山':'いしばしたんざん','長岡半太郎':'ながおかはんたろう','デリー・スルタン朝':'でりーするたんちょう'}
for word,reading in checks.items():assert any(x['word']==word and x['reading']==reading for x in items),word
assert '2026年' in next(x for x in items if x['word']=='シウダ・デ・ラ・パス')['meaning']
assert '国会' in next(x for x in items if x['word']=='ケープタウン')['meaning']
assert '正式な首都はアムステルダム' in next(x for x in items if x['word']=='ハーグ')['meaning']
assert '連邦都市' in next(x for x in items if x['word']=='ベルン')['meaning']
for word in ['金','ロック','フランクリン','ピサロ','フェニックス','バレッタ','コロンビア']:
 assert len([x for x in rows if x['word']==word])>=2,word
assert s['categories']==dict(collections.Counter(x['category'] for x in items))
print(json.dumps(dict(passed=True,added=2000,total=len(rows),states=50,stateCapitals=50,baselineBytePreserved=True,categories=s['categories']),ensure_ascii=False))
