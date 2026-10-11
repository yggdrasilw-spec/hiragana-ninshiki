# しりとりの画像・語彙修正（2026-10-11）

以下は第1回の履歴です。追加の76画像・83注文と現在の件数・ID対応は[第2回修正記録](shiritori-corrections-round2-2026-10-11.md)を参照してください。

指定52画像・64注文を処理し、共有先の語義を確認した。画像を変更する必要がない説明修正や単語削除も含むため、更新画像は45枚。6枚の生成元シートと不採用コマの理由を保存した。

辞書は6,191行から6,120行へ。20項目を削除、表記重複と誤読から生じた重複51項目を統合した。53項目の読みを修正し、1,780項目では説明の冒頭にある単純な見出し語の反復を機械的に除いた。

同じ読みでも別の意味は残す。駅／液、暑い／厚い、園児／臙脂、焼き餅／やきもちなどは保持。低学年で一般的な表記（生き物のカタカナ、食べ物のひらがな等）を優先し、その他は標準的な漢字表記を使用する。液／えきは液、液体／えき体は液体へ統合。最低の難易度を引き継ぐ。

あてるは、物を体などに接触させる意味に修正した。馬乗りには馬の背に乗る意味もあるが、今回は物を両脚でまたぐ意味と画像に合わせた。愛らしい（いじらしい）は誤った表記なので、いじらしいに修正した。

## 記録と再現

- [適用方針と語義・読みの修正](../data/corrections/2026-10-11-plan.json)
- [全変更の前後・削除理由・元IDと現在IDの対応](../data/corrections/2026-10-11-ledger.json)
- [生成プロンプト・採用と不採用・コマ位置](../data/corrections/2026-10-11-images.json)
- [全件の自動品質点検](../data/corrections/2026-10-11-quality.json)
- [画像の由来と全共有先](../assets/shiritori/manifest.json)

IDはCSVの行番号なので、削除後に変わる。注文のIDはoriginalIdとして保存し、画像点検記録とmanifestの共有先は現在のIDへ更新した。過去の説明レビューはその時点のIDのまま保存し、履歴の差分を検証してから旧テスト用に復元する。現在データは別の回帰テストで全注文と語義の対応を検査する。

再実行は `python scripts/apply-shiritori-corrections.py`。適用済みなら変更せずハッシュを確認し、後の変更を古い計画で上書きしない。原画像はsheetsに保存済みなので、生成時の一時パスがなくても由来を確認できる。

## 全件自動点検と限界

全6,120語と参照画像1,469枚を点検。読みの形式、CSV、画像破損、寸法、manifest、共有先、説明循環、表記重複、下部境界、JMdictの表記・読みを同じ基準で照合した。構造エラー・単語だけを繰り返す説明・同一説明の重複候補は0件。

JMdictは語の表記と読みの照合に使い、未収録だけで語を削除していない。固有名詞・自然な複合語・略称が多く含まれる。辞書の同じ表記が別の語義だった場合（鞍馬、利根など）も、自動で誤読と断定しない。

追加確認候補として、辞書未収録1,573件、辞書の読みとの差5件、今回作り直していない共有画像210件、下部境界が疑わしい既存画像122件を記録した。これらは誤りを確定した数ではない。今回の45画像は切り出し後に目視し、余白の警告2件は場面内の余白と確認した。辞書全体の意味・表情まで全件目視で合格したという記録にはしていない。

再点検: `python scripts/audit-shiritori-quality.py --dictionary /path/to/JMdict_e.gz`。JMdictは https://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz から取得し、作業日時とファイルのSHA256を品質記録に保存。リポジトリには辞書本文を複製しない。辞書を省略した実行は構造と画像の点検だけになり、辞書照合済みとは記録しない。

## 再発防止

新しい語の取り込みは、バッチCSVと同名の `.review.json` に各行の `reading`、`word`、`meaning`、`lexicalSource`（辞書や公式資料などの根拠）、`meaningReason`、`ageReason` を必要とする。画像がある場合は全共有先との対応を `imageReason` に記録。同じ読みの語を追加する場合は、表記違いでなく別語義である理由を `distinctSenseReason` に記録する。

例: `node scripts/import-shiritori-words.cjs batch.csv --validate-only` で書き込み前に全件検証する。過去のバッチを再指定しても、削除語・統合語・修正前の説明を再追加しない。根拠文字列があることだけで語義の真偽を証明できるわけではなく、曖昧なものは品質記録を確認する。

## 検証

- 64注文の対応、同音異義語保持、語義ごとの画像分離、全manifest共有先、差分の復元ハッシュを確認。
- 全参照画像のファイル存在・破損・登録・寸法・点検記録との一致を確認。
- PC 1280pxとスマホ390pxで更新画像を使う64語を表示。語義切り替え、説明、256px画像、クレジット、横のはみ出しを確認。
- 画像点検画面の保存・再開・下書き・注文出力・JSON往復・320/390px表示を検証。
- 説明・音声の既存テストとPC/スマホ3サイズの表示を検証。
- 既存2バッチの再取り込みは追加0件。未レビュー語の拒否、同音異義語の理由要求、削除語の再追加防止を検証。

ブラウザー環境の指定: `QA_EXECUTABLE=/usr/bin/chromium node tests/shiritori-correction-browser.cjs`。スクリーンショットはqa-output/correctionsへ保存（Git管理外）。

## 指定注文の対応表

| 元ID | 元の単語 | 現在ID／処理 | 修正後の画像 |
|---:|---|---|---|
| 59 | 遊び | 59・遊び | [toy.png](../assets/shiritori/toy.png) |
| 287 | いじくる | 284・いじくる | [toy.png](../assets/shiritori/toy.png) |
| 291 | 弄り | 288・弄り | [toy.png](../assets/shiritori/toy.png) |
| 70 | 暑い | 70・暑い | [review-0070.png](../assets/shiritori/review-0070.png) |
| 72 | 厚い | 72・厚い | [complete-0072.png](../assets/shiritori/complete-0072.png) |
| 75 | あてる | 75・あてる | [complete-0075.png](../assets/shiritori/complete-0075.png) |
| 76 | 後 | 76・後 | [complete-0076.png](../assets/shiritori/complete-0076.png) |
| 93 | 炙り | 92・炙り | [complete-0093.png](../assets/shiritori/complete-0093.png) |
| 96 | 炙る | 95・炙る | [complete-0093.png](../assets/shiritori/complete-0093.png) |
| 99 | 甘え | 98・甘え | [review-0099.png](../assets/shiritori/review-0099.png) |
| 100 | 甘える | 99・甘える | [review-0099.png](../assets/shiritori/review-0099.png) |
| 423 | 卑しい | 419・卑しい | [review-0423.png](../assets/shiritori/review-0423.png) |
| 150 | 改めて | 148・改めて | [complete-0150.png](../assets/shiritori/complete-0150.png) |
| 152 | 粗挽き | 150・粗挽き | [complete-0152.png](../assets/shiritori/complete-0152.png) |
| 169 | 有った丈 | 167・ありったけ | [complete-0169.png](../assets/shiritori/complete-0169.png) |
| 172 | あるある | 170・あるある | [complete-0172.png](../assets/shiritori/complete-0172.png) |
| 174 | アルカリ性 | 172・アルカリ性 | [complete-0174.png](../assets/shiritori/complete-0174.png) |
| 214 | いかにも | 212・いかにも | [complete-0214.png](../assets/shiritori/complete-0214.png) |
| 215 | 烏賊曳き | 削除 | — |
| 224 | 息 | 221・息 | [complete-2239.png](../assets/shiritori/complete-2239.png) |
| 240 | 戦 | 237・戦 | [review-0240.png](../assets/shiritori/review-0240.png) |
| 290 | 愛らしい | 287・いじらしい | [review-0290.png](../assets/shiritori/review-0290.png) |
| 298 | 何方 | 295・何方 | [complete-0298.png](../assets/shiritori/complete-0298.png) |
| 305 | 依然 | 302・依然 | [complete-0305.png](../assets/shiritori/complete-0305.png) |
| 307 | 急ぎ | 304・急ぎ | [review-0307.png](../assets/shiritori/review-0307.png) |
| 308 | 急ぐ | 305・急ぐ | [review-0307.png](../assets/shiritori/review-0307.png) |
| 318 | 居たたまれない | 315・居たたまれない | [complete-0318.png](../assets/shiritori/complete-0318.png) |
| 321 | 至って | 318・至って | [complete-0321.png](../assets/shiritori/complete-0321.png) |
| 325 | 至り | 322・至り | [complete-0325.png](../assets/shiritori/complete-0325.png) |
| 361 | 一気 | 358・一気 | [complete-0361.png](../assets/shiritori/complete-0361.png) |
| 372 | 一心同体 | 369・一心同体 | [review-0372.png](../assets/shiritori/review-0372.png) |
| 374 | 一寸 | 371・一寸 | [complete-0374.png](../assets/shiritori/complete-0374.png) |
| 391 | 一分 | 削除 | — |
| 420 | 嫌 | 416・嫌 | [kirai.png](../assets/shiritori/kirai.png) |
| 421 | いやいや | 417・いやいや | [kirai.png](../assets/shiritori/kirai.png) |
| 424 | 嫌だ | 420・嫌だ | [kirai.png](../assets/shiritori/kirai.png) |
| 425 | 嫌な | 421・嫌な | [kirai.png](../assets/shiritori/kirai.png) |
| 435 | 要る | 431・要る | [complete-0435.png](../assets/shiritori/complete-0435.png) |
| 478 | 印字 | 473・印字 | [complete-0475.png](../assets/shiritori/complete-0475.png) |
| 489 | 隠蔽 | 484・隠蔽 | [review-0489.png](../assets/shiritori/review-0489.png) |
| 524 | 薄い | 518・薄い | [complete-0524.png](../assets/shiritori/complete-0524.png) |
| 531 | 嘘 | 524・嘘 | [complete-0531.png](../assets/shiritori/complete-0531.png) |
| 539 | うたたね | 532・うたたね | [review-0539.png](../assets/shiritori/review-0539.png) |
| 548 | 団扇 | 540・団扇 | [complete-0548.png](../assets/shiritori/complete-0548.png) |
| 572 | 鵜の目 | 564・鵜の目 | [complete-0572.png](../assets/shiritori/complete-0572.png) |
| 580 | 馬乗り | 572・馬乗り | [complete-0580.png](../assets/shiritori/complete-0580.png) |
| 588 | 埋め合わせ | 580・埋め合わせ | [complete-0588.png](../assets/shiritori/complete-0588.png) |
| 612 | 上引き | 削除 | — |
| 654 | えき | 645・液へ統合 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 655 | 液 | 645・液 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 658 | 液体 | 648・液体 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 659 | えき体 | 648・液体へ統合 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 711 | 遠位 | 削除 | — |
| 720 | 延期 | 708・延期 | [complete-0720.png](../assets/shiritori/complete-0720.png) |
| 722 | 婉曲 | 710・婉曲 | [complete-0722.png](../assets/shiritori/complete-0722.png) |
| 737 | 遠心 | 724・遠心 | [complete-0737.png](../assets/shiritori/complete-0737.png) |
| 752 | 演奏 | 738・演奏 | [neiro.png](../assets/shiritori/neiro.png) |
| 754 | 援走 | 削除 | — |
| 756 | 延長 | 741・延長 | [complete-0756.png](../assets/shiritori/complete-0756.png) |
| 761 | 円転 | 削除 | — |
| 765 | 園農 | 削除 | — |
| 801 | 大勢 | 783・大勢 | [complete-0801.png](../assets/shiritori/complete-0801.png) |
| 810 | 大幅 | 792・大幅 | [complete-0810.png](../assets/shiritori/complete-0810.png) |
| 811 | 大昼寝 | 削除 | — |
