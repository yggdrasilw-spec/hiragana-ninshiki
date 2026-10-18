"""Write delivery records only after all batch and browser checks pass."""
import csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-culture512'
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
plan=read(OUT/'plan.json');summary=read(OUT/'summary.json');checks=read(OUT/'data-validation.json');browser=read(OUT/'browser-validation.json')
assert checks['passed'] and browser['passed']
inventory_path=ROOT/'data/image-coverage/r2-assets.json';inventory=read(inventory_path)
upload=read(OUT/'r2-upload.json');assert len(upload['entries'])==480
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in (ROOT/'qa-output/culture512-r2-transfer.jsonl').read_text(encoding='utf-8').splitlines()) if x.get('verified')}
assert all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in upload['entries'])
journal={x['bucket']+'/'+x['key']:x for x in (json.loads(l) for l in (ROOT/'qa-output/culture512-r2-transfer.jsonl').read_text(encoding='utf-8').splitlines()) if x.get('verified')}
readbacks=[journal[e['bucket']+'/'+e['key']] for e in upload['entries']]
(OUT/'r2-readback-validation.json').write_text(json.dumps(dict(passed=True,publicImages=480,entries=readbacks),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
entries={e['key']:e for e in inventory['entries']}
for e in upload['entries']:
 assert e['bucket']=='shiritori-images'
 assert e['key'] not in entries or entries[e['key']]['sha256']==e['sha256']
 entries[e['key']]=e
inventory['entries']=[entries[k] for k in sorted(entries)]
inventory['dictionaryImageReferences']=len({r['image_asset'] for r in csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')) if r['image_asset']})
inventory['revision']=hashlib.sha256(json.dumps(inventory['entries'],sort_keys=True).encode()).hexdigest()
inventory_path.write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
doc='''# 物語・酒・武器兵器・文化芸術の512項目（2026-10-19）

512項目・512読みを新規追加。画像は480枚を生成し、芸術家の短い名前と正式名の32組では同じ画像を共有した。たとえば「もね」「くろーどもね」は同じ人物を示す。芸術家の絵は画材・仕事・題材を表す説明イラストであり、本人の肖像や本人の作品の複製ではない。

物語64件は知名度と児童向け再話に接する機会を目安にレベル1〜4へ編集上分類した。認知率調査の結果ではない。残る448件はユーザー指定に従いレベル5。既存の意味別難易度と辞書の行順は保持した。

| 分野 | 項目数 |
| --- | ---: |
| おとぎ話・昔話・民話・関連する児童文学 | 64 |
| 酒類 | 64 |
| 武器・兵器・伝説と空想の武器 | 80 |
| 芸術家名（正式名の別読み32件を含む） | 96 |
| 世界遺産・構成資産・関連地名 | 80 |
| 伝統工芸品・関連する技法 | 64 |
| 広島県の文化財・工芸・芸能 | 32 |
| 国宝・関連する重要文化財など | 32 |

国宝・重要文化財・世界遺産の構成資産・一般の工芸技法を混同しないよう説明を分けた。「富貴寺」は「ふきじ」、「仏国寺」は「ぶっこくじ」。先行する神話512件の登録後にIDを付け直し、重なった神具3件は「オーディンの槍」「トールの槌」「天の瓊矛（あまのぬほこ）」の別呼称に変更した。同じ神具を別の実物とは説明しない。

画像は16語ずつ、30枚の4×4シートからマゼンタ罫線を実測して切り出した。うち4シートは内容を修正。焙煎麦、建物の裳階と門の上階、朱塗り、瓦葺、絵巻の場面、観音立像、屋根の形式などを直して再検証した。図は対象の代表的な特徴を説明するもので、文化財の実測図や同定写真ではない。

採用画像480枚だけを既存の配信バケットへ転送し、すべて読み戻して容量とSHA-256を照合。原本34シートと不採用・ID変更前の切り出し544枚はローカルに保管し、今回の公開転送には含めていない。Gitには画像本体を含めず、辞書・画像参照・プロンプト・出典・切り出しと確認の記録を保存する。

参考資料は国立国会図書館、国税庁、国立西洋美術館、東京富士美術館、UNESCO、文化庁、広島県、福山市、伝統的工芸品産業振興協会など。出典・語義・年齢・画像の判断理由は plan.json と research-notes.json、取り込みレビューに記録した。

## 確認

辞書履歴・語義・読み・5段階の難易度・画像共有32組を照合。PC 1280pxとスマホ390pxで全512項目の意味と画像をゲーム詳細・画像点検ページに表示し、代表語の実入力と同音異義語の切り替えを確認。画像は実際のR2配信を使い、ローカル画像への代替を禁止した。検証結果は同バッチの data-validation.json と browser-validation.json に保存。

## 登録内容

| ID | 読み | 表記 | レベル | 意味 |
| --- | --- | --- | ---: | --- |
'''
doc+='\n'.join(f'| {x["id"]} | {x["reading"]} | {x["word"]} | {x["grade"]} | {x["meaning"]} |' for x in plan['items'])+'\n'
(ROOT/'docs/shiritori-culture512-2026-10-19.md').write_text(doc,encoding='utf-8')
data=ROOT/'SHIRITORI_DATA.md';text=data.read_text(encoding='utf-8');line='\n物語・酒・武器兵器・文化芸術512項目（画像480枚＋正式名の共有32件）は [追加記録](docs/shiritori-culture512-2026-10-19.md) を参照。\n'
if 'shiritori-culture512-2026-10-19.md' not in text:data.write_text(text+line,encoding='utf-8')
print('Delivery documentation written for 512 verified meanings')
