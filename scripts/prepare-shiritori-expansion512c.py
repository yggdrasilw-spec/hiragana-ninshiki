"""Freeze current dictionary, resolve lexical evidence and prepare a reviewed intake.

Does not change the live dictionary. Modern terms use separately recorded primary
sources; dictionary presence alone is never an age or meaning approval.
"""
import csv, hashlib, json, re, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-15-expansion512c'
OUT=ROOT/'data/dictionary-imports'
COVER=ROOT/'data/image-coverage'/NAME
COVER.mkdir(parents=True,exist_ok=True)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
norm=lambda s:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s).replace('・','')
sourcepath=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json')
dictionary=json.loads(sourcepath.read_text(encoding='utf-8'))
index={}
for e in dictionary['words']:
 for k in e['kana']:index.setdefault(norm(k['text']),[]).append((e,k))
words={}
for line in (OUT/(NAME+'-candidates.txt')).read_text(encoding='utf-8').splitlines():
 for term in line.split('|'):
  rd,word=term.strip().split(' ',1);words.setdefault(rd,word)
# Prefer everyday short forms, familiar concrete vocabulary and current play.
# Drop less familiar, redundant and more technical candidates from this batch.
exclude=set('む よ り ろ らじかせ ゆーま えすいー でぃーじぇー じーぴーえす まいくろえすでぃー えるいーでぃー ぴーでぃーえふ ゆーあーるえる あいでぃー えーあーる ぶいあーる すりーでぃー つーでぃー ぴーてぃーえー えーえるてぃー えーいーでぃー ゆーふぉー えすえふ えぬぴーしー りもーとこんとろーる ぎが いんでっくす あるごりずむ こーど せきゅりてぃー ふぃるたりんぐ ぷらいばしー こじんじょうほう ゆーざー ゆーざーめい あかうんと ろぐあうと しもんにんしょう かおにんしょう にだんかいにんしょう よそくへんかん しゅつりょく はーどうぇあ そふとうぇあ でじたる ぴくせる えでぃたー れいやー じんこうちのう ちゃっとぼっと じどうほんやく おんせいごうせい がぞうにんしき がぞうせいせい おんせいにんしき くろすぷれい もぶ ばーちゃるげーむかーど ふぁんくらぶ さいりうむ とれんど ふぉろー ふぉろわー とうろくしゃ ねちけっと さいせいりすと ていそくさいせい おーでぃおぶっく ぽっどきゃすと でじたるふぉとふれーむ ふぉとぶーす ふぉとすぽっと うぉーたーしゅーず すたいらす あどれす さんどぼっくすげーむ すぴーどらん けーぽっぷ じぇいぽっぷ ひっぷほっぷ ぱるくーる しょーとかっときー ほーむぽじしょん しふときー ばっくすぺーすきー'.split())
authored=[]
exclude.update('でぃーぶいでぃー はりつけ れいんぶーつ えすえぬえす'.split())
exclude.discard('ほーむぽじしょん')
for line in (OUT/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
 if not line or line.startswith('#'):continue
 rd,meaning,group,*lv=line.split('|')
 if rd in exclude:continue
 authored.append(dict(reading=rd,word=words[rd],meaning=meaning,group=group,level=int(lv[0]) if lv else 1))
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
rules=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)',line,re.I)
 rules.append((m[1].lower(),norm(m[2].strip())) if m else ('contains',norm(line)))
old={r['reading'] for r in live}
pairs=[]
for line in (OUT/(NAME+'.abbreviations.txt')).read_text(encoding='utf-8').splitlines():
 if not line or line.startswith('#'):continue
 short,full,word,meaning=line.split('|')
 pairs.append(dict(abbreviation=short,fullReading=full,fullWord=word))
 if full not in old and full not in {x['reading'] for x in authored}:
  previous=next((l.split('|') for l in (OUT/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines() if l.startswith(full+'|')),None)
  assert meaning or previous,(short,full)
  authored.append(dict(reading=full,word=word,meaning=meaning or previous[1],group=previous[2] if previous else word,level=2))
assert len(authored)>=512
missing=[];reviews=[]
for i,x in enumerate(authored,len(live)+1):
 rd=x['reading'];assert rd not in old
 assert re.fullmatch('[ぁ-ゖー]+',rd) and not re.search('[,\r\n]',x['meaning'])
 assert not any(rd==p if m=='exact' else p in rd for m,p in rules),rd
 canonical=lambda t:unicodedata.normalize('NFKC',t).replace(' ','').casefold()
 matches=[(e,k) for e,k in index.get(rd,[]) if set(k['tags'])<={'sk'} and canonical(x['word']) in [canonical(k['text']),*(canonical(j['text']) for j in e['kanji'])]]
 matches=[(e,k) for e,k in matches if any(not s['dialect'] and not set(s['misc'])&{'obs','arch','vulg','derog'} for s in e['sense'])]
 x.update(id=i,imageStatus='planned')
 if matches:
  e,k=matches[0]
  x.update(entryId=e['id'],sourceKana=k['text'],lexicalSource=f"JMdict {e['id']} / {dictionary['dictDate']}",sources=['https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+e['id']])
 else:missing.append({k:x[k] for k in ('reading','word','meaning')})
 x.update(meaningReason='今回扱う意味は次の独自説明に限定。'+x['meaning'],
  ageReason=('低学年の身近な遊び・道具・食事・端末操作に結びつく言葉。短いかな中心の説明を用意。' if x['level']==1 else 'しくみや社会的な関係の理解が必要なのでレベル2。'),
  definitionAuthor='独自作成（2026-10-15）',reviewStatus='editorially-reviewed')
 reviews.append(x)
save(COVER/'draft.json',dict(name=NAME,date='2026-10-15',baselineRows=len(live),baselineSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),items=reviews))
save(COVER/'needs-primary-evidence.json',missing)
save(COVER/'abbreviation-pairs.json',pairs)
print(json.dumps(dict(selected=len(reviews),excluded=len(exclude),single=sum(len(x['reading'])==1 for x in reviews),jmdict=len(reviews)-len(missing),needsEvidence=[x['word'] for x in missing]),ensure_ascii=False))
