"""Separate, resumable editorial intake; never overwrite preceding batches."""
import csv, hashlib, json, re, unicodedata
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-16-expansion1024f'
DATA=ROOT/'data/dictionary-imports'; OUT=ROOT/'data/image-coverage'/NAME
OUT.mkdir(parents=True,exist_ok=True)
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return unicodedata.normalize('NFKC',s).casefold().translate(str.maketrans({chr(i):chr(i-96) for i in range(0x30a1,0x30f7)})).replace('・','').replace(' ','')
live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')))
old={norm(x['word']) for x in live}; readings={x['reading'] for x in live}
rules=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 line=line.strip()
 if not line or line.startswith('#'):continue
 m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)',line,re.I)
 rules.append((m[1].lower(),norm(m[2])) if m else ('contains',norm(line)))
items=[];excluded=[];seen=set();seenrd=set()
# Curated homonyms: preserve the other sense; never reuse its image.
distinct=set('クー ボス マッチ スバル スマート ジャガー ミニ ガイア ミライ ノート サクラ イグニス パレット カタナ コルト レックス ルポ インパラ コンパス ゴースト マーブル コロン ゼロ さやえんどう いちごみるく 水星 レア パン パック サイフ コカブ エライ 山彦 覚 麒麟 鳳凰 ピクシー タイタン アトラス カペラ ミラ ゴルフ エアリアル トッポ エリーゼ コースター'.split())
general=set('コーラ フルーツオレ ミニサラミ 梅ジャム のど飴 レーズンサンド アーモンドチョコレート マカダミアチョコレート'.split())
for line in (DATA/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
 if not line.strip() or line.startswith('#'):continue
 if line.startswith('['):category,policy,source=line[1:-1].split('|');continue
 fields=line.split('|');name=fields[0];word,rd=name.split('~') if '~' in name else (name,norm(name))
 meaning=fields[1]
 homonym=word in distinct
 reason=None if homonym else 'existing-spelling' if norm(word) in old else 'existing-reading' if rd in readings else 'duplicate-spelling' if norm(word) in seen else 'duplicate-reading' if rd in seenrd else None
 if not re.fullmatch('[ぁ-ゖー]+',rd):reason='invalid-reading'
 hits=[p for mode,p in rules if (rd==p if mode=='exact' else p in rd)]
 if any(rd==p for mode,p in rules):reason='blacklist-exact'
 if reason:excluded.append(dict(word=word,reading=rd,reason=reason,category=category));continue
 assert not any(c in meaning for c in ',\r\n'),word
 assert len(meaning)>=9,word
 seen.add(norm(word));seenrd.add(rd)
 image_policy='generate' if word in general else policy
 if word in general:meaning=meaning.split('。')[0]+'。' if word in ['梅ジャム','ミニサラミ','のど飴'] else meaning
 items.append(dict(word=word,reading=rd,meaning=meaning,category=category,imagePolicy=image_policy,sources=[source],level=3 if image_policy=='none' or category in ['恒星','衛星','妖怪・幻想生物'] else 2,**({'distinctSenseReason':'既存の同音語は別の対象。今回の説明で会社・商品・天体・競技・伝承の対象を限定し、画像も語義ごとに分離する。'} if homonym else {}),**({'blacklistSubstringReview':dict(hits=hits,decision='語全体では飲食物・メーカー・競技・天体・伝承等の適切な名称。部分一致だけの誤検知。')} if hits else {})))
save(OUT/'candidates.json',items);save(OUT/'exclusions.json',excluded)
print(json.dumps(dict(eligible=len(items),categories=Counter(x['category'] for x in items),imagePolicies=Counter(x['imagePolicy'] for x in items),excluded=Counter(x['reason'] for x in excluded)),ensure_ascii=False))
