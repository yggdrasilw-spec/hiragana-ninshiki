# 確認済みの辞書由来の追加語

見出し語・読みの確認元は JMdict（James William BREEN / Electronic Dictionary Research and Development Group）。
このディレクトリの派生語彙データと独自作成の説明は **CC BY-SA 4.0** で提供。
原辞書の語義・翻訳・例文は転載していない。今回扱う意味、年齢、検索語を個別に確認した。

- [辞書の説明](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)
- [EDRDG の利用条件](https://www.edrdg.org/edrdg/licence.html)
- [CC BY-SA 4.0 全文](https://creativecommons.org/licenses/by-sa/4.0/legalcode)

2026-10-11は日常・学校生活の24語を追加。保存画像は追加していない。
既存の画像検索が不発ならプレースホルダーになる。検索画像の語義一致まで確認済みとはしない。
レギュラーはスポーツの先発選手、ループは輪の形など、説明と検索語の意味を限定。

```sh
node scripts/import-shiritori-words.cjs data/dictionary-imports/2026-10-11-school-life.csv --validate-only --append
node scripts/import-shiritori-words.cjs data/dictionary-imports/2026-10-11-school-life.csv --append
```

追加は末尾へ行い、既存の画像ID・順序・CPUの既存候補順を維持する。
`history.json` に前後のハッシュと追加行を記録する。古い修正記録は書き換えない。
履歴を逆にたどって元のCSVへ戻せることを、既存の回帰テストで確認する。
画像のみの追加も `type: image-assets` として同じ履歴に記録する。変更前後の各行とハッシュを保存し、語・読み・説明・難易度・検索語を変えていないことを検証する。2026-10-11の追加画像32語も記録済み。
同じバッチの再実行は追加0件。定期的に最新辞書との照合を行い、採用済み語の読み・表記も確認する。
