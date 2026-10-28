# 日本の地名・駅名の追加辞書

2026-10-28登録。通常の `whitelist.csv` と意味別難易度決定には追記せず、独立した追加辞書として管理する。

## 登録数と使い方

| 種類 | 意味の件数 |
| --- | ---: |
| 町域 | 83,452 |
| 駅名 | 8,499 |
| 市区町村 | 2,780 |
| 「市」を付けない市名 | 743 |
| 都道府県 | 46 |
| 合計 | 95,520 |

元の通常辞書に存在していた地名は維持する。上表の46都道府県は既存登録分を除いた追加数であり、都道府県を1つ欠落させた数ではない。全47都道府県の原資料を使用している。

追加辞書は85,326種類の読み。通常辞書20,957種類と重なる読み1,140種類を統合すると、全体は105,143種類になる。同じ読みの普通名詞・地名・駅名は、表記・意味・出典を別々に保持する。

設定の「日本の地名・駅名（約9.5万件）も使う」で有効にする。初期状態はOFF。CPUが使う「日本の地名・駅名」ジャンルは追加辞書のON/OFFとは独立して選べる。大量の固有名詞を小学低学年の一般語として扱わないため、この追加辞書の意味別難易度はレベル5とする。子どもが入力した地名は、追加辞書がONなら選択レベルやCPUジャンルに関係なく認める。

入力補正と手書きの辞書照合には、ONになっている全辞書の読み索引を使う。「しんしらおが」から「しんしらおか（新白岡）」を提示し、候補の説明だけを取得する動作をブラウザで検証した。

## 管理と配信

- `data/japan-places/entries.jsonl`: 安定したID、読み、名称、種類、所在地、原資料のレコード・駅コード、レベルを持つ管理用原本。
- `data/japan-places/metadata.json`: 件数、原本SHA-256、資料の版・取得時点・ライセンス・スナップショットSHA-256、除外件数。
- `data/dictionary-imports/japan-geography-sources/`: 照合用の郵便住所・駅のスナップショット。
- `data/shiritori-delivery/japan-places/index.json`: ON時だけ取得する軽量索引。原本と通常辞書の版を束縛する。
- `data/shiritori-delivery/japan-places/chunks/`: 1ファイル最大128読み。706ファイル、最大109,800バイト。必要な語の説明・頭文字の候補だけ取得する。

通常起動時に追加辞書へのリクエストは発生しない。ON時の索引取得は2,862,579バイトであり、約31MBの管理用原本をブラウザに配らない。読み索引は全読みを含む。配信サイズは非圧縮値で、手書きモデル等を除く。

取得に失敗したON操作は、通常辞書を利用できる状態に戻す。CPUの候補取得失敗は勝敗に変換しない。通常辞書と追加辞書の版が合わない場合は有効化を停止し、再生成を求める。

## 出典と確認範囲

地名は[日本郵便のUTF-8郵便番号データ](https://www.post.japanpost.jp/service/search/zipcode/download/utf-zip.html)、駅は[station_database / Seo-4d696b75](https://github.com/Seo-4d696b75/station_database)の2026年9月30日版を使用。駅データは[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)で、地名・読みを抽出し所在地説明を作成した。アプリの設定と駅名の説明にも著作者・出典・ライセンス・加工の旨を表示する。ゲームの画像や画面は利用しない。

95,520件すべてについて、名称・読み・所在地と原資料の対応を検証した。廃駅、開業日前の駅、郵便用の注記、複数町域を一括した表記、数字の読みを推定する必要がある住所などは除外する。地名の全網羅や、2026年9月30日以降の改称・開廃を保証するものではない。出典照合は現地調査や全項目の人手校閲とは異なる。

除外・既存登録の詳細は、収集時の `data/dictionary-imports/2026-10-27-japan-geography.*` に残す。旧候補の行IDやCSVのレベル3は引き継がず、安定IDと意味別レベル5を設定した。

## 更新と検証

収集済み候補と原資料の照合・登録は `python -X utf8 scripts/import-shiritori-geography.py --write`。`--write`を付けなければ照合だけを行う。ステージングのレビューJSONとスナップショットを使い、通常CSVを変更しない。

配信ファイルの生成は `node scripts/build-shiritori-delivery.cjs`、一致検証は同コマンドの `--check`。従来の `python scripts/build-shiritori-grade-bands.py` からも通常辞書に続いて追加辞書を自動生成する。通常辞書を更新すると重複読みの集計も再生成される。

検証コマンド:

```
node tests/shiritori-delivery.cjs
node tests/shiritori-geography.cjs
node tests/shiritori-delivery-browser.cjs
node tests/shiritori-geography-browser.cjs
node tests/shiritori-settings-browser.cjs
node tests/shiritori-multiplayer.cjs
```

ブラウザ検証にはPlaywrightが必要。10万種類超の読みからの近似候補検索は検証PC上で約81～82msだった。スマホ幅の画面でも確認したが、実際の低速端末の処理性能や子どもの自然な手書き認識精度を測った数値ではない。
