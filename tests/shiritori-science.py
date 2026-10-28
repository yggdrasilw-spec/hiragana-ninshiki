"""Check the intake, preserved baseline, grade/source joins and corrected concepts."""
import csv,json,hashlib,collections,re,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'data/dictionary-imports/2026-10-28-science'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));raw=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(raw.decode('utf-8').splitlines()))
baseline=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+1])+b'\n'
assert hashlib.sha256(baseline).hexdigest()==s['beforeSha256']
assert s['registered'] and len(items)==s['added'] and len(rows)>=s['baselineRows']+len(items)
prefix=b'\n'.join(raw.split(b'\n')[:s['baselineRows']+len(items)+1])+b'\n';assert hashlib.sha256(prefix).hexdigest()==s['afterSha256']
assert len({(x['reading'],x['word'],x['meaning']) for x in items})==len(items)
assert len({(x['reading'],x['meaning']) for x in items})==len(items)
grades=read(ROOT/'data/shiritori-grade-review.json');coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');updates=read(ROOT/'data/image-coverage/review-updates.json');metadata=[json.loads(l) for l in (ROOT/'data/science/entries.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(grades)==len(coverage)==len(updates['entries'])==len(rows)
assert updates['csvSha256']==hashlib.sha256(raw).hexdigest()
assert len(metadata)==len(items)
for x,m in zip(items,metadata):
 r=rows[x['id']-1];assert all(r[k]==str(x[k]) for k in r)
 assert re.fullmatch('[ぁ-ゖー]+',x['reading']) and not any(c in x['meaning'] for c in ',\n\r')
 assert x['image_mode']=='none' and not x['image_asset'] and x['grade']==5
 assert grades[x['id']-1]['level']==5 and coverage[x['id']-1]['status']=='explanation-only'
 assert updates['entries'][x['id']-1]['text']==[x['reading'],x['word'],x['meaning']]
 assert all(m[k]==x[k] for k in ['reading','word','meaning','genre']) and m['source']['url']==x['source']['url']
 assert x['source']['kind']!='wordnet','Ambiguous WordNet fallbacks were replaced editorially'
 if x['source']['kind']=='tomoshi':assert 'AI補助' in m['source']['title'] and 'definitionOrigin' in x['source']
 assert not re.search(r'同音の漢字|書きかえ|語義\d+|^\d+\.',x['meaning'])
checks={'卵割':('らんかつ','受精卵'),'仕事':('しごと','エネルギー'),'摂動':('せつどう','近似'),'レプトン':('れぷとん','素粒子'),'硝化':('しょうか','アンモニア'),'核':('かく','核膜'),'細胞膜':('さいぼうまく','脂質'),'同化':('どうか','合成'),'ホルンフェルス':('ほるんふぇるす','変成岩'),'光束':('こうそく','ルーメン'),'太陽日':('たいようじつ','24時間'),'陰極':('いんきょく','還元'),'陽極':('ようきょく','酸化'),'クーロンの法則':('くーろんのほうそく','点電荷'),'分散':('ぶんさん','波長')}
for word,(reading,term) in checks.items():assert any(x['word']==word and x['reading']==reading and term in x['meaning'] for x in items),word
assert not any(x['word']=='卵割' and x['reading']=='かいわり' for x in items)
assert dict(collections.Counter(x['category'] for x in items))==s['categories']
with sqlite3.connect('file:'+str(ROOT/'data/science/catalog.sqlite')+'?mode=ro',uri=True) as db:
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 assert db.execute('SELECT count(*) FROM entries').fetchone()[0]==len(items)
 assert db.execute("SELECT count(*) FROM search WHERE search MATCH 'エネルギー'").fetchone()[0]>10
core=read(ROOT/'data/science/core-coverage.json');assert core['missing']==[] and len(core['items'])==958
print(json.dumps(dict(passed=True,added=len(items),total=len(rows),baselineBytePreserved=True,coreChecks=len(core['items']),categories=s['categories']),ensure_ascii=False))
