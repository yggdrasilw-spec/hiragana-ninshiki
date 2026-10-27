"""Prepare a reviewed, explanation-only high-school vocabulary intake."""
import csv, json, hashlib, collections, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-28-highschool'
sha=lambda b:hashlib.sha256(b).hexdigest()
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert not (BASE.with_suffix('.summary.json').exists() and json.loads(BASE.with_suffix('.summary.json').read_text(encoding='utf-8')).get('registered')), 'Batch already registered; preserve its review and stable IDs'
raw=(ROOT/'whitelist.csv').read_bytes()
old=list(csv.DictReader(raw.decode('utf-8').splitlines()))
inventory=[json.loads(x) for x in (ROOT/'data/external-dictionaries/jmdict/candidate-inventory.jsonl').read_text(encoding='utf-8').splitlines()]
lookup={x['reading']:x for x in inventory}
sources={
 '倫理': ['https://www.kobe-kosen.ac.jp/education/syllabus/2026/html/C2_1011020.html','https://www.pref.hiroshima.lg.jp/uploaded/attachment/215003.pdf'],
 '情報': ['https://www.mext.go.jp/a_menu/shotou/zyouhou/detail/mext_01831.html','https://www.mext.go.jp/content/20200928-mxt_jogai01-100013300_001.pdf','https://www.mext.go.jp/content/20200722-mxt_jogai02-100013300_006.pdf','https://www.ipa.go.jp/shiken/asia/qv6pgp0000002s9q-att/000027072.pdf'],
 '古典': ['https://www.mext.go.jp/content/20250410-mxt_kyoiku01-100002620_02.pdf','https://tbqr.sanseido-publ.co.jp/09-seisenkoten/contents/koten-bunpo-list/','https://irweb.kawahara.ac.jp/uhe_syllabus/SyllabusDetail.aspx?jc=COM30001&jn=2022','https://japanknowledge.com/introduction/keyword.html?i=1796']}
items=[];excluded=[];cat=None;seen=set()
for line in BASE.with_suffix('.candidates.tsv').read_text(encoding='utf-8').splitlines():
 if '|' not in line:cat=line;continue
 reading,word,meaning=line.split('|')
 assert re.fullmatch('[ぁ-ゖー]+',reading),(reading,word)
 assert ',' not in line and len(meaning)>10
 # Existing words retain their current sense and level. No spelling variants added.
 present=[dict(reading=x['reading'],word=x['word'],meaning=x['meaning']) for x in old if x['word']==word]
 if present:excluded.append(dict(reading=reading,word=word,reason='既存の同表記語を保持し再追加しない',existing=present));continue
 assert (reading,word) not in seen;seen.add((reading,word))
 inv=lookup.get(reading)
 matched=bool(inv and word in inv['words'])
 evidence=dict(method='既存JMdict見出し索引との読み・表記一致' if matched else '教科の標準用語・古語を編集確認。独立辞書見出し確認とは区別',references=sources[cat],reviewedOn='2026-10-28')
 if matched:evidence.update(dictionary='JMdict',entries=inv['entries'],reading=reading,word=word)
 x=dict(id=len(old)+len(items)+1,reading=reading,word=word,meaning=meaning,imagequery=word,level='3',imagequery_en='',image_asset='',image_mode='none',image_credit='',grade=5,category=cat,lexicalSource=evidence,
   meaningReason='高校'+cat+'の文脈に限定し独自の短文で説明。'+meaning,
   ageReason='高校'+cat+'の専門語義として「はってん」に配置。小学生向け候補には含めない。',
   imageReason='抽象概念・文法・古語の意味を短い説明で示す。保存画像と外部画像検索は使わない。')
 hom=[y for y in old if y['reading']==reading]
 if hom:x['distinctSenseReason']='同じ読みの既存語（'+'／'.join(y['word'] for y in hom)+'）とは意味を区別する。今回の意味は「'+meaning+'」。'
 items.append(x)
header=raw.decode('utf-8').splitlines()[0].split(',')
with BASE.with_suffix('.csv').open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=header,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(items)
save(BASE.with_suffix('.review.json'),items);save(BASE.with_suffix('.excluded.json'),excluded)
s=dict(registered=False,baselineRows=len(old),beforeSha256=sha(raw),added=len(items),categories=dict(collections.Counter(x['category'] for x in items)),newReadings=len({x['reading'] for x in items}-{x['reading'] for x in old}),endingN=sum(x['reading'].endswith('ん') for x in items),dictionaryIndexMatches=sum('entries' in x['lexicalSource'] for x in items),explanationOnly=len(items))
save(BASE.with_suffix('.summary.json'),s)
save(BASE.with_suffix('.sources.json'),dict(retrievedOn='2026-10-28',references=sources,policy='科目範囲の資料と語形の辞書確認を区別。定義は独自作成。編集確認のみの語は個別レビューで明示。古語の読みは歴史的綴りではなく現代の発音に合わせる。'))
print(json.dumps(s,ensure_ascii=False))
print('追加: '+' / '.join(x['word'] for x in items))
print('既存のため除外: '+' / '.join(x['word'] for x in excluded))
