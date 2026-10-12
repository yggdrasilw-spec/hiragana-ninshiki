# 表記違いの統合と未作成画像256語の追加（2026-10-12）

同じ読み・意味を持つ28組を点検し、75注文の修正ですでに統合されていた2組を除く26組を新たに一つの項目に統合し、未作成の256語に保存画像を追加した。64語の第3バッチに続き、96語の第4バッチと96語の第5バッチを追加した。画像未設定の全項目の補完はまだ完了していない。

現在の辞書は6,521行。保存画像があるのは2,627行、未設定は3,894行（うちレベル1は1,137行）。参照される画像ファイルは2,245枚。画像未設定の項目は従来の写真検索を利用する。

75注文の意味18語・画像54枚の修正を保持した。統合対象のイチゴと月（天体）には、75注文で修正された新しい画像を優先して割り当てた。カエルとシカはすでに統合済みとして記録する。

## 表記の統合

アリ／蟻、イカ／烏賊、イチゴ／苺、オオカミ／狼、カエル／蛙、亀／カメ、カラス／烏、キノコ／茸、キリン／麒麟、クジラ／鯨、クモ／蜘蛛、コイ／鯉、コケ／苔、サケ／鮭、サンマ／秋刀魚、ザクロ／石榴、シカ／鹿などを統合した。同一対象の説明の詳しさの違いを別語義とはしない。難易度は統合対象の最小値を採用し、既存の保存画像を維持した。

イカ／以下、カエル／帰る、雲／クモ、食べ物と春の雨の春雨、生物のウニと食べる部分の海胆、府県と都市など、意味が異なる項目は維持した。読みの異なる別名は今回の統合対象ではない。

削除した行と統合先、変更前後の内容、全行の対応、辞書の前後ハッシュは `data/corrections/2026-10-12-variants.json` に保存した。取り込み履歴から以前の辞書を完全に復元できる。参照がなくなった3画像の登録情報は同ファイルに退避し、元の画像ファイルも保持した。画像マニフェストの全共有先ID、画像点検記録、現行IDを使う追加画像計画、確認画面の更新情報を同期した。

`import-shiritori-words.cjs` は今回の統合を含む `reviewed-corrections` の履歴も参照する。古いバッチの再取り込みで削除した表記が復活しないことを検証した。

## 画像と調査

食べ物、衣服、日用品、道具、学校用品、建物・場所などを優先した。4×4シート16枚と単独修正4枚をImageGenで作り、原画像・生成指示・語義・切り出し座標・目視確認内容を保存した。全256枚を256×256へ切り出し、縮小一覧でも確認した。実際のコマ境界を使い、区切り線を除き、縦横比を維持した。隣のコマの混入は切り出し座標の修正で解消した。茶碗と籠の周囲に残った細い灰色の枠も、対象と影を残して除去した。

生物は代表種を明確にして資料と照合してから生成した。魚種全体に固有種の特徴を一般化しない。恐竜の色は復元上の表現である。

- 鯵：マアジを代表種とし、側線のゼイゴなどを確認。[新潟市水族館](https://www.marinepia.or.jp/picturebook/fish/entry-11835.html)
- 穴子：マアナゴを代表種とし、白点列と鰭の構造を確認。[環境省](https://www.env.go.jp/water/heisa/heisa_net/setouchiNet/seto/g1/g1chapter1/ikimono/anago.html)、[宮城県](https://www.pref.miyagi.jp/soshiki/mtsc/maanago.html)
- アパトサウルス：長い首と鞭状の尾を確認。初回は尾が短いため不採用とし、全身の単独画像を作り直した。[米国国立公園局](https://www.nps.gov/places/apatosaurus-louisae.htm)、[アメリカ自然史博物館](https://www.amnh.org/exhibitions/dinosaurs-ancient-fossils/sauropod-biomechanics/a-strange-tale)
- アンキロサウルス：低い四足の体、骨質の装甲、棍棒状の尾を確認。[ロンドン自然史博物館](https://www.nhm.ac.uk/discover/dino-directory/Ankylosaurus.html)

オムレツも初回が巻き卵焼き状だったため不採用とし、折り畳んだ卵と柔らかな断面を示す画像に作り直した。コンパスは針と円の中心が一致しない図を不採用とし、道具の構造を示す単独画像に変更した。そろばんは[日本珠算連盟](https://www.shuzan.jp/gakushu/history/06.html)で現行日本式の上珠1つ・下珠4つと菱形の珠を確認し、7軸の全珠数と形を照合して再生成した。博物館の展示例は特定の恐竜種の図鑑として使用しない。

- 辞書への登録：`data/batches/2026-10-12-wave{3,4,5}-images.csv`
- 調査・目視確認：`data/image-coverage/2026-10-12-wave{3,4,5}/image-review.json`
- 語義・生成指示・座標：同フォルダーの `registered-plan.json`
- 全画像の確認一覧：同フォルダーの `final-review.jpg`
- 画像の由来と共有先：`assets/shiritori/manifest.json`
- 原シート：`assets/shiritori/sheets/2026-10-12-wave*.png`

切り出しと登録は以下で再現できる。保持した原シートを使い、再取り込みは追加0枚になる。

```sh
python scripts/integrate-shiritori-supplements.py --wave wave3
python scripts/integrate-shiritori-supplements.py --wave wave4
python scripts/integrate-shiritori-supplements.py --wave wave5
python scripts/build-shiritori-review-updates.py
```

## 検証

全6,521行・2,245参照画像の構造エラーと参照切れは0件。今回追加した256画像に自動点検の追加候補はない。既存の画像に対するヒューリスティックの確認候補は引き続き残してあり、全既存画像を今回再レビューしたという意味ではない。

辞書データ、修正履歴の復元、表記統合、同音異義語の保持、難易度、統合した表記の再取り込み防止を検証した。過去の64注文、83注文、103注文、辞書取り込みの検証も合格。画像確認画面のPC・スマホ表示、更新順、保存・読み込み、○×・修正注文の操作を検証した。

追加256語すべてをPC（1280px）・スマホ（390px）の両方でゲーム内に表示し、写真検索が失敗しても正しい保存画像・見出し・説明・クレジットが表示されることを確認した。画像確認画面の「今回画像を補完した単語」にも256語すべて含まれ、正しい画像と意味が表示された。ページエラーとゲーム画面の横はみ出しは0件。

```sh
node tests/shiritori-data.cjs
node tests/shiritori-variants.cjs
node tests/shiritori-import-history.cjs
node tests/shiritori-corrections.cjs
node tests/shiritori-round2.cjs
node tests/shiritori-review93.cjs
node tests/shiritori-jmdict.cjs
node tests/shiritori-meaning.cjs
python tests/shiritori-word-image75.py
python scripts/audit-shiritori-image-coverage.py
python scripts/audit-shiritori-quality.py
node tests/shiritori-supplement-browser.cjs
node tests/shiritori-image-review.cjs
```
