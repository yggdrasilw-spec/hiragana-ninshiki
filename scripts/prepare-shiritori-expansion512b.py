"""Validate independently authored words and plan sense-specific shared pictures.

Use the frozen full JMdict outside the repository. No live dictionary mutation.
"""
import csv,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-14-expansion512b'
OUT=ROOT/'data/dictionary-imports'
IMAGES=ROOT/'data/image-coverage'/NAME
IMAGES.mkdir(parents=True,exist_ok=True)
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
source_path=Path(sys.argv[1])
blob=source_path.read_bytes()
assert hashlib.sha256(blob).hexdigest()=='25eb58f942c3847b8379599a687e2c4b194d7eb2bfccfad2eff7be671a11e097'
source=json.loads(blob)
norm=lambda s: ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
applies=lambda xs,v:'*' in xs or v in xs
blocked={'arch','obs','rare','obsc','vulg','sens','derog','sl','X','dated'}
WORDS={'いっとう':'一等','うえ':'上','かいちょう':'快調','かわり':'代わり','かんじょう':'感情',
 'けいかい':'軽快','げんそく':'減速','じどう':'自動','せいとう':'正当','せんさい':'繊細','はやい':'速い'}
SENSES={'あつかう':[0,2],'ひくい':[0,1,2],'やすむ':[1]}
NORMAL=set('あいよう あいつぐ あたりまえ あてはまる あてはめる あどりぶ あなろぐ あまちゅあ あらためる あらわす ありがち いいかえる いいきる いきわたる いちじてき うけいれる うけつぐ うけつける うみだす うやまう おおざっぱ おぎなう おこなう おりじなる かいがい かいちょう かがくてき かくう かんじょう かんじる かんりゃく がいこく がいぶ きびしい きりかえる けいかい げきれい げんざい げんそく こくない こけい こころみる ことなる こべつ したがう しぶい しんじる じっさい じつぶつ じつわ じどう じどうてき じはつてき じゅうだい じゅんすい じょうとう じんそく せいとう せいみつ せんさい そうご そうしょく そうべつ そうほう たもつ たんか たんどく だいよう ちょうき ちょうほう ちょうわ とりけす なじむ ねんいり のべる やくだつ むずかしい'.split())
index={}
for e in source['words']:
 for k in e['kana']:index.setdefault(norm(k['text']),[]).append((e,k))
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
baseline=live[:7609]
assert len(baseline)==7609
old={r['reading'] for r in baseline}
rules=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)',line,re.I)
 rules.append((m[1].lower(),norm(m[2].strip())) if m else ('contains',norm(line)))
authored=[]
for line in (OUT/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
 cols=line.split('|');rd,meaning=cols[:2];group=cols[2] if len(cols)>2 else rd
 authored.append(dict(reading=rd,meaning=meaning,group=group))
assert len(authored)==512
assert len({x['reading'] for x in authored})==512
reviews=[]; extracts=[]; issues=[]
for x in authored:
 rd=x['reading']
 assert rd not in old and re.fullmatch('[ぁ-ゖー]{2,}',rd) and not rd.endswith('ん'),rd
 assert not any(rd==p if m=='exact' else p in rd for m,p in rules),rd
 assert x['meaning'].endswith('。') and not re.search('[,\r\n]',x['meaning']),rd
 candidates=[]
 for e,k in index.get(rd,[]):
  if k['tags']:continue
  forms=[j for j in e['kanji'] if applies(k['appliesToKanji'],j['text']) and not j['tags']]
  word=next((j['text'] for j in forms if j['common']),forms[0]['text'] if forms else k['text'])
  if rd in WORDS:
   if WORDS[rd] not in [j['text'] for j in forms]:continue
   word=WORDS[rd]
  for si,s in enumerate(e['sense']):
   if set(s['misc'])&blocked or s['dialect']:continue
   if not applies(s['appliesToKana'],k['text']) or (forms and not applies(s['appliesToKanji'],word)):continue
   if not any(p in {'n','num','adj-na','adj-no','vs','vs-i','vs-s','adj-i'} or p.startswith(('v1','v5')) for p in s['partOfSpeech']):continue
   candidates.append((not k['common'],si,e,k,word,s))
 if not candidates:issues.append(rd);continue
 _,si,e,k,word,s=sorted(candidates,key=lambda c:c[:2])[0]
 sense_indexes=SENSES.get(rd,[si])
 for n in sense_indexes:
  assert applies(e['sense'][n]['appliesToKana'],k['text']) and applies(e['sense'][n]['appliesToKanji'],word)
 x.update(id=7609+len(reviews)+1,word=word,level=2 if rd in NORMAL or re.search('[\u3400-\u9fff]',x['meaning']) else 1)
 url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+e['id']
 reviews.append(dict(**x,entryId=e['id'],sourceKana=k['text'],senseIndexes=sense_indexes,partOfSpeech=s['partOfSpeech'],
  lexicalSource=f"JMdict {e['id']} / {source['dictDate']} / {url}",sources=[url],
  meaningReason='対象語義の動作・性質・用途に限定した独自の説明。'+x['meaning'],
  ageReason='身近な動作・性質を具体的な短い文で説明。抽象的な関係・学習語・漢字を含む説明はレベル2。',
  reviewStatus='editorially-reviewed',definitionAuthor='独自作成（2026-10-14）',imageStatus='planned',
  imageReason='同じ場面で対象語義を示せる語だけを共有する。共有元と理由は画像計画に記録。'))
 extracts.append(dict(reading=rd,word=word,entryId=e['id'],sourceKana=k['text'],senseIndex=sense_indexes[0],senseIndexes=sense_indexes,
  kanaAppliesToKanji=k['appliesToKanji'],appliesToKana=s['appliesToKana'],appliesToKanji=s['appliesToKanji'],
  partOfSpeech=s['partOfSpeech'],misc=s['misc'],dialect=s['dialect']))
 print(rd+'|'+word+'|'+str(si)+'|'+'; '.join(g['text'] for g in s['gloss']))
assert not issues,issues
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save(OUT/(NAME+'.review.json'),reviews)
save(OUT/(NAME+'.source.json'),dict(dictDate=source['dictDate'],version=source['version'],sourceSha256=hashlib.sha256(blob).hexdigest(),
 attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',licenseUrl='https://www.edrdg.org/edrdg/licence.html',rows=extracts))
save(IMAGES/'authored-plan.json',dict(name=NAME,date='2026-10-14',baselineRows=len(baseline),baselineSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),items=reviews))
print(json.dumps({'eligible':len(reviews),'levels':{n:sum(x['level']==n for x in reviews) for n in (1,2)}},ensure_ascii=False))
