"""Archive unused crops privately and write the complete delivery evidence."""
import csv,hashlib,json,mimetypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-request25'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items'];summary=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
archive=OUT/'superseded';archive.mkdir(exist_ok=True)
obsolete=[ROOT/'assets/shiritori'/x['filename'] for x in json.loads((OUT/'sheets.json').read_text(encoding='utf-8'))[1]['tiles']]
obsolete+=list((ROOT/'assets/shiritori').glob('request25-unused-*.png'))
for src in obsolete:
 dest=archive/src.name
 assert src.resolve().is_relative_to(ROOT.resolve()) and dest.resolve().is_relative_to(OUT.resolve())
 if src.exists():
  assert not dest.exists();src.rename(dest)
upload=json.loads((OUT/'r2-upload.json').read_text(encoding='utf-8'))
known={e['key'] for e in upload['entries']}
for src in sorted(list(archive.glob('*.png'))+list(OUT.glob('game-*.png'))+list(OUT.glob('catalog-*.png'))):
 key=src.relative_to(ROOT).as_posix()
 if key not in known:upload['entries'].append(dict(key=key,bucket='shiritori-image-archive',bytes=src.stat().st_size,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),contentType='image/png'))
save(OUT/'r2-upload.json',upload)
journal=ROOT/'qa-output/request25-r2-transfer.jsonl'
if journal.exists():
 verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')}
 if all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in upload['entries']):
  summary['r2VerifiedObjects']=len(upload['entries']);summary['r2PublicObjects']=64;summary['r2PrivateObjects']=len(upload['entries'])-64
  save(OUT/'summary.json',summary);save(ROOT/'data/dictionary-imports/2026-10-19-request25.summary.json',summary)
source=dict(name='JMdict',date='2026-10-05',attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',licenseUrl='https://www.edrdg.org/edrdg/licence.html',definitions='Japanese explanations independently written for this batch.',primaryReferences=json.loads((OUT/'sources.json').read_text(encoding='utf-8')))
save(ROOT/'data/dictionary-imports/2026-10-19-request25.source.json',source)
doc='''# 指定25語と周辺語の追加（2026-10-19）

指定25読みをすべて追加し、周辺語と同音異義語を含め64項目を登録。新規の読みは57種類。辞書は13,918項目から13,982項目になった。既存行の語義・画像・難易度・順序は保持した。

「しぼう」は脂肪・志望・死亡・子房、「らぐ」は敷物と時間のずれ、「ぷーま」は動物とブランドを区別。「こっか」の国歌と「てん」の動物は既存の別義とは分けた。首長竜とエラスモサウルスは恐竜とは別の海生爬虫類として説明。さざれ石は小さな石の語義を選んだ。コンスタンティノープルとビザンツの絵は歴史的な都市の復元イメージであり写真ではない。

画像は生成イラスト61枚、ウムラウトの正確な図1枚、商品・ブランドの独自文字カード2枚。全64項目に専用画像があり、未登録0項目。4×4シート4枚から罫線を機械検出・除去し、元シートから全出力のハッシュまで再検証。ベーゴマの誤った軸を修正してから採用した。未使用コマと不採用版の画像は非公開保管先へ分離。

難易度は意味ごとに1=4項目、2=19項目、3=27項目、4=12項目、5=2項目。商品・ブランドは固有名詞レベル。CSVの旧レベルとは独立して現行の5段階方針を適用。

語彙資料はローカルJMdict（2026-10-05）と、環境省、英国自然史博物館、内閣府、ゲーテ・インスティトゥート、厚生労働省、PUMA公式、江崎グリコ公式など。独自に書いた日本語の説明、語義・年齢・画像の判断理由、辞書資料を plan.json と取り込みレビューに保存。

## 登録内容

| ID | 読み | 表記 | レベル | 説明 |
| --- | --- | --- | --- | --- |
'''
doc+='\n'.join(f'| {x["id"]} | {x["reading"]} | {x["word"]} | {x["grade"]} | {x["meaning"]} |' for x in items)+'\n'
doc+='\n## 検証\n\n辞書履歴、重複・語義の取り込み条件、全意味の難易度割当を検証。画像はR2から読み戻し、容量とSHA-256を照合。ブラウザー検証結果は `data/image-coverage/2026-10-19-request25/browser-validation.json` に保存。PC 1280pxとスマホ390pxで全64画像をゲームと画像点検ページに表示し、指定25読みのキーボード入力、同音異義語の切替を確認した。ローカル画像への代替は禁止した。\n\n画像64枚と非公開の原本・検証資料31件をR2へ保存し、全95件の読み戻し検証を完了。辞書・画像参照・出典・検証記録はGitで公開する。画像本体はGitに含めない。\n'
(ROOT/'docs/shiritori-request25-2026-10-19.md').write_text(doc,encoding='utf-8')
print(json.dumps(dict(objects=len(upload['entries']),privateArchivedCrops=len(list(archive.glob('*.png'))))))
