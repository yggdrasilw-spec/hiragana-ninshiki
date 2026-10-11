# しりとり画像・語彙修正 第2回（2026-10-11）

指定76画像・83注文を処理し、語義ごとの共有先を確認しました。説明・見出しのみの修正も含むため、実際に更新した画像は70枚（既存55枚、新規15枚）です。辞書は6,144語から6,143語へ変更しました。

「痛」を「痛い」、「書き算」を「筆算」、「割入」を「割り込む」、「着合う」を「コーディネート」、「居合わせ」を「居合わせる」に修正。「噛みやん」は削除し、その画像ファイルを「噛む」へ引き継いで作り直しました。「一指」は一本の指という語義を説明し、「指す」と画像を分けました。

「いやいや」「機動」「おてんば」「劣る」「寝坊と遅刻」「齧り付くと噛む」「借り暮らし」「可愛い」「感覚」「カンカン」「監督」「起案」「決別」などは語義に応じて分離しました。お話・告げる・伝えるは口頭で伝える場面、艱難辛苦・堅忍・タフ・忍耐は苦しい登山の場面、賢い・賢明・注意は安全な踏み台を選ぶ場面で共有しています。

7枚の生成元を保存。「虚ろ」の初回コマは驚いた表情に見えたため不採用とし、単独画像で再生成しました。生成シートの行・列は均等とは限らないため、白い区切り線を実測して各コマのcropBoxを記録しています。切り出し後の70枚すべてを再点検し、隣のコマの混入を除き、縦横比を保持して256×256へ縮小しました。

## 記録

- [83注文の前後・元IDと現在ID・削除理由](../data/corrections/round2/ledger.json)
- [修正計画](../data/corrections/round2/plan.json)
- [全生成プロンプト・切り出し座標・採用と不採用](../data/corrections/round2/images.json)
- [元の共有画像の語義点検](../data/corrections/round2/shared-review.json)
- [検証結果](../data/corrections/round2/verification.json)・[回帰テスト結果](../data/corrections/round2/test-results.json)
- [構造・画像品質の監査](../data/corrections/round2/quality.json)
- [manifest](../assets/shiritori/manifest.json)・[現在の単語別点検記録](../data/image-coverage/review-2026-10-10.json)

注文IDは今回の修正直前の行番号です。削除後の現在IDと区別し、manifest・点検記録・追加32画像の選定IDを更新しました。過去の取り込み記録と第1回の修正記録は保持しています。今回の変更をハッシュ付きの履歴に追加し、全変更を逆順に戻すと過去の辞書を正確に復元できることを検証しました。「噛みやん」や変更前の説明が古いバッチから再追加されることも防いでいます。

## 検証

全6,143語・1,515参照画像の存在・破損・寸法・manifestの全共有先・点検記録を照合し、構造エラー0件。今回の70画像の境界検出警告0件。PC 1280pxとスマホ390pxで注文・共有先99語ずつの画像と説明を表示し、語義切り替え、256px画像、横のはみ出しを検証しました。画像点検画面の保存・再開・下書き・注文出力・JSON往復・32追加語の表示・320/390px表示も合格しました。

語彙・説明・旧64注文・履歴復元・取り込み品質・取り込み履歴・辞書監査の回帰テストは合格しました。既存の未修正画像について、共有語義の確認候補187件と下部境界の確認候補109件を監査に残しています。誤りを確定した数ではなく、今回の70画像は含みません。外部辞書の追加照合や、辞書全体の意味・表情の全件目視合格を示す記録ではありません。

```sh
node tests/shiritori-round2.cjs
python scripts/audit-shiritori-image-coverage.py
python scripts/audit-shiritori-quality.py --output data/corrections/round2/quality.json
CORRECTION_LEDGER=data/corrections/round2/ledger.json QA_EXECUTABLE=/usr/bin/chromium node tests/shiritori-correction-browser.cjs
QA_EXECUTABLE=/usr/bin/chromium node tests/shiritori-image-review.cjs
```

`python scripts/apply-shiritori-round2.py` は適用済みならハッシュを確認するだけです。`--recrop` は保存済みの実測座標から画像を再作成し、辞書を変更しません。

## 注文の対応表

| 注文ID | 修正前 | 現在ID・処理 | 画像 |
|---:|---|---|---|
| 311 | 痛 | 311・痛い | [itami.png](../assets/shiritori/itami.png) |
| 344 | 一番 | 344・一番 | [complete-0347.png](../assets/shiritori/complete-0347.png) |
| 345 | 一部 | 345・一部 | [complete-0348.png](../assets/shiritori/complete-0348.png) |
| 346 | 一面 | 346・一面 | [complete-0349.png](../assets/shiritori/complete-0349.png) |
| 364 | 一指 | 364・一指 | [round2-0364.png](../assets/shiritori/round2-0364.png) |
| 365 | 一周 | 365・一周 | [complete-0368.png](../assets/shiritori/complete-0368.png) |
| 382 | 一致 | 382・一致 | [complete-0385.png](../assets/shiritori/complete-0385.png) |
| 385 | 一定 | 385・一定 | [complete-0388.png](../assets/shiritori/complete-0388.png) |
| 397 | 稲光 | 397・稲光 | [complete-0401.png](../assets/shiritori/complete-0401.png) |
| 413 | 芋づる | 413・芋づる | [complete-0417.png](../assets/shiritori/complete-0417.png) |
| 417 | いやいや | 417・いやいや | [round2-0417.png](../assets/shiritori/round2-0417.png) |
| 462 | 所謂 | 462・所謂 | [complete-0467.png](../assets/shiritori/complete-0467.png) |
| 466 | 印 | 466・印 | [complete-0471.png](../assets/shiritori/complete-0471.png) |
| 486 | 引力 | 486・引力 | [complete-0491.png](../assets/shiritori/complete-0491.png) |
| 500 | 羽化 | 500・羽化 | [complete-0505.png](../assets/shiritori/complete-0505.png) |
| 502 | うがい | 502・うがい | [complete-0507.png](../assets/shiritori/complete-0507.png) |
| 524 | 嘘 | 524・嘘 | [complete-0531.png](../assets/shiritori/complete-0531.png) |
| 526 | 嘘つき | 526・嘘つき | [complete-0533.png](../assets/shiritori/complete-0533.png) |
| 549 | 虚ろ | 549・虚ろ | [complete-0557.png](../assets/shiritori/complete-0557.png) |
| 580 | 埋め合わせ | 580・埋め合わせ | [complete-0588.png](../assets/shiritori/complete-0588.png) |
| 608 | 運転 | 608・運転 | [complete-0617.png](../assets/shiritori/complete-0617.png) |
| 1432 | 機動 | 1431・機動 | [round2-1432.png](../assets/shiritori/round2-1432.png) |
| 645 | 液 | 645・液 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 648 | 液体 | 648・液体 | [complete-0654.png](../assets/shiritori/complete-0654.png) |
| 710 | 婉曲 | 710・婉曲 | [complete-0722.png](../assets/shiritori/complete-0722.png) |
| 711 | 演技 | 711・演技 | [complete-0723.png](../assets/shiritori/complete-0723.png) |
| 724 | 遠心 | 724・遠心 | [complete-0737.png](../assets/shiritori/complete-0737.png) |
| 775 | 大きい | 775・大きい | [complete-0792.png](../assets/shiritori/complete-0792.png) |
| 776 | 大きさ | 776・大きさ | [complete-0793.png](../assets/shiritori/complete-0793.png) |
| 792 | 大幅 | 792・大幅 | [complete-0810.png](../assets/shiritori/complete-0810.png) |
| 799 | 公 | 799・公 | [complete-0818.png](../assets/shiritori/complete-0818.png) |
| 803 | お帰り | 803・お帰り | [complete-0822.png](../assets/shiritori/complete-0822.png) |
| 812 | お代わり | 812・お代わり | [complete-0831.png](../assets/shiritori/complete-0831.png) |
| 819 | 置く | 819・置く | [complete-0838.png](../assets/shiritori/complete-0838.png) |
| 829 | 教え | 829・教え | [ss-lecture.png](../assets/shiritori/ss-lecture.png) |
| 1567 | 教育 | 1566・教育 | [ss-lecture.png](../assets/shiritori/ss-lecture.png) |
| 1574 | 教授 | 1573・教授 | [ss-lecture.png](../assets/shiritori/ss-lecture.png) |
| 831 | お仕置き | 831・お仕置き | [complete-0850.png](../assets/shiritori/complete-0850.png) |
| 833 | お支度 | 833・お支度 | [complete-0852.png](../assets/shiritori/complete-0852.png) |
| 863 | 落ちる | 863・落ちる | [complete-0882.png](../assets/shiritori/complete-0882.png) |
| 864 | お使い | 864・お使い | [complete-0883.png](../assets/shiritori/complete-0883.png) |
| 872 | おてんば | 872・おてんば | [round2-0872.png](../assets/shiritori/round2-0872.png) |
| 888 | 劣る | 888・劣る | [round2-0888.png](../assets/shiritori/round2-0888.png) |
| 894 | 驚く | 894・驚く | [odoroku.png](../assets/shiritori/odoroku.png) |
| 896 | お腹の空く | 896・お腹の空く | [onakanosuku.png](../assets/shiritori/onakanosuku.png) |
| 911 | お寝坊 | 911・お寝坊 | [round2-0911.png](../assets/shiritori/round2-0911.png) |
| 913 | 各々 | 913・各々 | [complete-0934.png](../assets/shiritori/complete-0934.png) |
| 920 | お話 | 920・お話 | [tsutaeru.png](../assets/shiritori/tsutaeru.png) |
| 937 | 溺れる | 937・溺れる | [sukuu.png](../assets/shiritori/sukuu.png) |
| 938 | おまけ | 938・おまけ | [omake.png](../assets/shiritori/omake.png) |
| 969 | 降りる | 969・降りる | [complete-0992.png](../assets/shiritori/complete-0992.png) |
| 972 | 折る | 972・折る | [origami.png](../assets/shiritori/origami.png) |
| 979 | お別れ | 979・お別れ | [ss-farewell.png](../assets/shiritori/ss-farewell.png) |
| 1021 | 帰る | 1021・帰る | [ss-farewell.png](../assets/shiritori/ss-farewell.png) |
| 984 | 恩恵 | 984・恩恵 | [complete-1007.png](../assets/shiritori/complete-1007.png) |
| 1034 | 書き算 | 1034・筆算 | [complete-1058.png](../assets/shiritori/complete-1058.png) |
| 1056 | 賢い | 1056・賢い | [round2-1056.png](../assets/shiritori/round2-1056.png) |
| 1065 | 齧り付く | 1065・齧り付く | [round2-1065.png](../assets/shiritori/round2-1065.png) |
| 1175 | 噛む | 1174・噛む | [complete-1199.png](../assets/shiritori/complete-1199.png) |
| 1066 | 貸す | 1066・貸す | [ss-lend.png](../assets/shiritori/ss-lend.png) |
| 1073 | 風 | 1073・風 | [complete-1097.png](../assets/shiritori/complete-1097.png) |
| 1075 | 数える | 1075・数える | [complete-1099.png](../assets/shiritori/complete-1099.png) |
| 1105 | 割入 | 1105・割り込む | [complete-1131.png](../assets/shiritori/complete-1131.png) |
| 1170 | 紙飛行機 | 1170・紙飛行機 | [kamihikouki.png](../assets/shiritori/kamihikouki.png) |
| 1173 | 噛みやん | 削除 | 噛むへ引き継ぎ |
| 1195 | 通う | 1194・通う | [complete-1222.png](../assets/shiritori/complete-1222.png) |
| 1198 | 空 | 1197・空 | [complete-1225.png](../assets/shiritori/complete-1225.png) |
| 1209 | 空っぽ | 1208・空っぽ | [complete-1236.png](../assets/shiritori/complete-1236.png) |
| 1215 | 借り | 1214・借り | [ss-borrow.png](../assets/shiritori/ss-borrow.png) |
| 1220 | 借り暮らし | 1219・借り暮らし | [round2-1220.png](../assets/shiritori/round2-1220.png) |
| 1217 | 仮 | 1216・仮 | [complete-1244.png](../assets/shiritori/complete-1244.png) |
| 1223 | 仮初め | 1222・仮初め | [complete-1250.png](../assets/shiritori/complete-1250.png) |
| 1248 | 可愛い | 1247・可愛い | [round2-1248.png](../assets/shiritori/round2-1248.png) |
| 1256 | 交わす | 1255・交わす | [ss-communicate.png](../assets/shiritori/ss-communicate.png) |
| 1271 | 感覚 | 1270・感覚 | [round2-1271.png](../assets/shiritori/round2-1271.png) |
| 1272 | 間隔 | 1271・間隔 | [complete-1301.png](../assets/shiritori/complete-1301.png) |
| 1273 | カンカン | 1272・カンカン | [round2-1273.png](../assets/shiritori/round2-1273.png) |
| 1307 | 監督 | 1306・監督 | [round2-1307.png](../assets/shiritori/round2-1307.png) |
| 1309 | 艱難辛苦 | 1308・艱難辛苦 | [nintai.png](../assets/shiritori/nintai.png) |
| 1372 | 着合う | 1371・コーディネート | [complete-1401.png](../assets/shiritori/complete-1401.png) |
| 1374 | 居合わせ | 1373・居合わせる | [complete-1403.png](../assets/shiritori/complete-1403.png) |
| 1375 | 起案 | 1374・起案 | [round2-1375.png](../assets/shiritori/round2-1375.png) |
| 1419 | 気体 | 1418・気体 | [complete-1448.png](../assets/shiritori/complete-1448.png) |
