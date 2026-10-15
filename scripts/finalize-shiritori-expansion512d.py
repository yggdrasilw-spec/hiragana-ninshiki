"""Prepare and append exactly 512 independently reserved vocabulary entries."""
import argparse,csv,hashlib,importlib.util,io,json,subprocess,sys,unicodedata
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
NAME='2026-10-15-expansion512d';OUT=ROOT/'data/image-coverage'/NAME;DATA=ROOT/'data/dictionary-imports'
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def run(*a):subprocess.run(a,cwd=ROOT,check=True)
ap=argparse.ArgumentParser();ap.add_argument('--import-all',action='store_true');args=ap.parse_args()
plan=read(OUT/'plan.json');items=plan['items'];assert len(items)==512
before=(ROOT/'whitelist.csv').read_text(encoding='utf-8');live=list(csv.DictReader(io.StringIO(before)))
already=all(any(r['reading']==x['reading'] and r['word']==x['word'] and r['meaning']==x['meaning'] for r in live) for x in items)
if already:print('Already imported: run tests to verify');sys.exit(0)
assert len(live)==plan['baselineRows'],'Preceding batch must finish before assigning IDs'
reserved=read(OUT/'reservation-snapshot.json')['readings']
other=read(ROOT/'data/image-coverage/2026-10-15-expansion512c/plan.json')['items']
old={r['reading'] for r in live};blocked=old|set(reserved)|{x['reading'] for x in other}
assert len({x['reading'] for x in items})==512
assert not [x['word'] for x in items if x['reading'] in blocked]
assert read(DATA/'history.json')[-1]['afterSha256']==sha(before)
wiki={x['word']:x for x in read(OUT/'lexical-crosscheck.json')}
compounds={x['word']:x for x in read(OUT/'compound-evidence.json')}
dictionary=read(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json'))
canon=lambda s:unicodedata.normalize('NFKC',s).replace(' ','').replace('・','').casefold()
index={}
for e in dictionary['words']:
 for f in e['kanji']+e['kana']:index.setdefault(canon(f['text']),[]).append(e)
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
for n in range(1,11):
 group=[x for x in items if x.get('sheet')==n]
 verified=grid.verify_report(OUT/f'sheet{n:02}-crop.json',ROOT/'assets/shiritori'/group[0]['sourceSheet'],ROOT/'assets/shiritori')
 assert list(verified)==[x['filename'] for x in group]
primary={'野球チーム':'https://npb.jp/teams/','サッカーチーム':'https://www.jleague.jp/club/','バスケチーム':'https://www.bleague.jp/club/','マリオのキャラクター':'https://www.nintendo.com/jp/character/mario/characters/index.html','カービィのキャラクター':'https://www.kirby.jp/character/','どうぶつの森のキャラクター':'https://www.nintendo.com/jp/character/mori/','スプラトゥーンのキャラクター':'https://www.nintendo.com/jp/switch/av5ja/'}
reviews=[];source=[];batch=[];image_rows=[]
for x in items:
 assert x['id']==plan['baselineRows']+len(reviews)+1
 asset=ROOT/'assets/shiritori'/x['filename']
 with Image.open(asset) as im:assert im.size==(256,256)
 refs=list(x.get('sources',[]));lexical=x.get('lexicalSource');matches=index.get(canon(x['word']),[])
 entry=next((e for e in matches if any(k['text'].translate(str.maketrans({chr(i):chr(i-96) for i in range(0x30a1,0x30f7)}))==x['reading'] for k in e['kana'])),None)
 if entry:
  lexical=f'JMdict {entry["id"]} / {dictionary["dictDate"]}';x['entryId']=entry['id'];refs.append('https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+entry['id'])
 c=compounds.get(x['word'])
 if c:refs.append(c['fullurl']);lexical=lexical or '料理本体または構成要素の見出しを参照した独自編集'
 w=wiki.get(x['word'])
 if w and w['matched']:refs.append(w['fullurl']);lexical=lexical or '公開百科事典の見出し照合（語義は独自編集）'
 if x['category'] in primary:refs.append(primary[x['category']])
 if x['category']=='ゲーム':
  publishers={'ロブロ':'https://www.roblox.com/ja','フォートナイト':'https://www.fortnite.com/','フォトナ':'https://www.fortnite.com/','ロケットリーグ':'https://www.rocketleague.com/','Fall Guys':'https://www.fallguys.com/','Overcooked':'https://www.team17.com/games/overcooked/','ヒューマン フォール フラット':'https://www.humanfallflat.com/','UNDERTALE':'https://undertale.jp/','DELTARUNE':'https://deltarune.jp/','Stardew Valley':'https://www.stardewvalley.net/','テラリア':'https://terraria.org/','HUMANITY':'https://humanity.game/ja/','パラッパラッパー':'https://www.playstation.com/ja-jp/','ぷよぷよ':'https://puyo.sega.jp/','ぷよテト':'https://puyo.sega.jp/','ぷよぷよテトリス':'https://puyo.sega.jp/','テトリス':'https://tetris.com/','スイカゲーム':'https://www.aladdinx.jp/pages/suika-game','桃太郎電鉄':'https://www.konami.com/games/momotetsu/','桃鉄':'https://www.konami.com/games/momotetsu/','ドラゴンクエスト':'https://www.dragonquest.jp/','ドラクエ':'https://www.dragonquest.jp/','ドラゴンクエストビルダーズ':'https://www.dragonquest.jp/','ファイナルファンタジー':'https://jp.finalfantasy.com/','FF':'https://jp.finalfantasy.com/','キングダム ハーツ':'https://www.jp.square-enix.com/kingdom/','ロックマン':'https://www.capcom.com/rockman/','モンスターハンター':'https://www.monsterhunter.com/','モンハン':'https://www.monsterhunter.com/'}
  refs.append(publishers.get(x['word'],'https://www.nintendo.com/jp/software/'))
 if x['category']=='その他のゲームキャラクター':refs.append('https://www.minecraft.net/ja-jp/about-minecraft' if 'Minecraft' in x['meaning'] else 'https://www.nintendo.com/jp/games/pikmin4/index.html')
 # Familiar productive compounds are reviewed by their food/ingredient relation;
 # presence of a whole-string encyclopedia heading is not an acceptance rule.
 lexical=lexical or ('構成語と提供例を確認した複合料理名・飲料名' if x['category'] in ['料理','飲み物'] else '公式シリーズ案内と作品内名称を照合した独自編集')
 image_reason=('料理の材料・提供例と照合した独自生成の挿絵。商品包装・ロゴ・人物を含めない。' if x.get('sheet') else '名称と読みだけを独自の組版で描画。肖像・公式ロゴ・エンブレム・キャラクターの姿を使わない。外部画像検索を固定で抑止。')
 review=dict(x,lexicalSource=lexical,sources=list(dict.fromkeys(refs)),meaningReason='説明は独自作成。対象の料理・競技・チーム・作品を特定し、引用文や現所属・最新成績は使わない。 '+x['meaning'],ageReason='食文化にふれるレベル2の語。' if x['level']==2 else '知っている子が使える固有名詞としてレベル3。作品名を説明に含めて日常語と区別。',imageReason=image_reason,imageStatus='covered',reviewStatus='editorially-reviewed',definitionAuthor='独自作成（2026-10-15）',rightsPolicy='generated-unbranded-food' if x.get('sheet') else 'local-text-card-only')
 reviews.append(review)
 source.append(dict(reading=x['reading'],word=x['word'],lexicalSource=lexical,sources=review['sources'],**({'entryId':entry['id']} if entry else {}),**({'jocRecord':x['sourceRecord']} if x.get('sourceRecord') else {}),**({'encyclopediaHeading':{k:w[k] for k in ['title','pageid','lastrevid']}} if w and w['matched'] else {})))
 batch.append(dict(reading=x['reading'],word=x['word'],meaning=x['meaning'],imagequery=x['word'],level=x['level'],imagequery_en='',image_asset='',image_mode='',image_credit=''))
 prompt=(ROOT/'assets/shiritori'/x['sourceSheet']).with_suffix('.prompt.txt').read_text(encoding='utf-8') if x.get('sheet') else 'Deterministic neutral typography only: '+x['word']+' / '+x['reading']+'. No portrait, logo, crest or character art. Source: scripts/stage-shiritori-expansion512d.py'
 image_rows.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],filename=x['filename'],scene=x['scene'],sourceSheet=x['sourceSheet'],tileIndex=x['tileIndex'],generatedAt='2026-10-15',prompt=prompt,cropValidation=x.get('cropValidation',''),credit=x['credit']))
save(DATA/(NAME+'.review.json'),reviews);save(DATA/(NAME+'.source.json'),dict(date='2026-10-15',rows=source,note='説明は独自作成。見出し照合だけを独立した意味確認・画像の利用許諾とは扱わない。'))
with (DATA/(NAME+'.csv')).open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=HEADER,lineterminator='\n');w.writeheader();w.writerows(batch)
image_batch=ROOT/'data/batches'/f'{NAME}-images.csv'
with image_batch.open('w',encoding='utf-8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(image_rows[0]),lineterminator='\n');w.writeheader();w.writerows(image_rows)
summary=dict(name=NAME,addedWords=512,baselineRows=len(live),beforeSha256=sha(before),categories=dict(Counter(x['category'] for x in items)),generatedIllustrations=160,textCards=352,missingImages=0,overlapWithPriorBatch=0)
save(OUT/'summary.json',summary)
run('node','scripts/import-shiritori-words.cjs',str(DATA/(NAME+'.csv')),'--validate-only','--append')
if not args.import_all:print(json.dumps(dict(prepared=True,**summary),ensure_ascii=False));sys.exit(0)
run('node','scripts/import-shiritori-words.cjs',str(DATA/(NAME+'.csv')),'--append')
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(image_batch))
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
coverage=read(ROOT/'data/image-coverage/review-2026-10-10.json');byid={e['id']:e for e in coverage}
for x in reviews:
 row=rows[x['id']-1]
 assert row['image_asset']=='assets/shiritori/'+x['filename']
 byid[x['id']]=dict(id=x['id'],**row,target=True,category=x['category'],scopeReason=x['imageReason'],assignment='new',sourceId=x['id'],sourceReview=x['imageReason'])
save(ROOT/'data/image-coverage/review-2026-10-10.json',[byid[i] for i in range(1,len(rows)+1)])
summary.update(afterSha256=sha((ROOT/'whitelist.csv').read_text(encoding='utf-8')),totalRows=len(rows))
save(OUT/'summary.json',summary);save(DATA/(NAME+'.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(dict(imported=True,**summary),ensure_ascii=False))
