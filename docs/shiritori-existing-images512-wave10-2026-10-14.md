# 既存語512語の画像追加（2026-10-14）

画像未登録だった既存語512語に画像を登録。単語・読み・意味・難易度・順序は変更していない。

- 専用イラスト：383語。16語×24シートを生成し、磁場の1語は正確な図へ変更。
- 数字・曜日・文字・単位・幾何・磁場などの図：129語。
- 登録直前：画像未登録2,818語。登録後：2,306語。
- 登録時の全辞書：7,609語。画像登録済み：5,303語。

作業中に別バッチで辞書が512語増えている。上記はこのバッチの登録直前／直後の実測値。今回の対象ID512件は初回計画のままで、新しい語の追加とは重複していない。

## 確認記録

- `data/image-coverage/2026-10-13-wave10/plan.json`：語ID・語義・コマ順・全プロンプト・修正版参照。
- `data/image-coverage/2026-10-13-wave10/validation/`：罫線の実測境界、切り出し、原画像／出力PNGハッシュ。
- `data/image-coverage/2026-10-13-wave10/diagram-validation.json`：図129枚のID・ハッシュ・再生成スクリプト。
- `data/image-coverage/2026-10-13-wave10/content-review.json`：512件の目視照合記録。
- `data/batches/2026-10-14-wave10-existing512.csv`：全512件の登録バッチ。
- `data/image-coverage/2026-10-13-wave10/preview.html`：今回追加した512語だけの検索可能な画像一覧。

画像は説明用イラスト／図として確認。地名の風景は実景写真ではなく、天体のイラストは精密星図ではない。語義との目視照合は専門資料の全件独立検証を意味しない。

## 修正して採用した主な箇所

脂を体内の脂肪層へ、綾織りを斜めの織り目へ変更。右脳は正面を向いた子の右半球を強調。菌からウイルスのような図形を除去。ジュゴンの二又の尾、ねぷたの扇形、ハドロサウルスとパラサウロロフスの区別、バジリスクの蛇の姿を確認。小数0.5・60度の角・月の満ち欠け・磁場は図を修正。

色漏れや不等寸のシートは登録を保留し、画像編集／再生成で修正。クロップは罫線を実測し、固定座標・固定率や検証緩和による回避はしていない。余白の大きさは合否条件にしていない。元シートと修正履歴を保持。

参考にした資料：

- [Reef Authority: Dugong](https://www.gbrmpa.gov.au/learn/animals/dugong)
- [弘前市観光情報: 弘前ねぷたまつり](https://hirosaki-kanko.or.jp/edit.html?id=cat02_summer_neputa)
- [Rutgers Geology Museum: Hadrosaurus](https://geologymuseum.rutgers.edu/about-us-geology-museum/mastodon-musings/mastodon-musings/255-the-story-of-new-jersey-s-state-fossil-hadrosaurus-foulkii)
- [なよろ市立天文台: 南斗六星](https://www.nayoro-star.jp/kitasubaru/astro/photogallery/asterism/southerndipper.html)

## 検証

`node tests/shiritori-data.cjs`、`node tests/shiritori-import-history.cjs`、`python -X utf8 scripts/audit-shiritori-image-coverage.py` が合格。全24枚の採用シートを元画像から再計算して照合済み。画像参照の破損は0件。

PC／スマホの全512語表示は `tests/shiritori-wave10-browser.cjs` で検査し、結果を `browser-validation.json` に保存する。

新規語512語分と既存語512語分を合わせ、1,024枚の画像更新としてコミット・プッシュ対象に含める。両バッチのID・画像参照・語義は重複／競合なし。PC・スマホで全1,024語をゲームと画像確認画面に表示して合格。統合検証記録：`data/image-coverage/2026-10-14-combined1024/`。
