# 一般的な読み4,262種類の追加語彙：出典と利用条件

対象は `scope.jsonl` に固定した4,262種類の読みです。各候補の採否と理由は
`decisions.jsonl`、採用した語の出典・説明・確認方法は
`../../dictionary-imports/2026-11-16-common4262.review.json` に記録します。

## 日本語の定義

一部の定義は、日本語版Wiktionaryの執筆者による文章を利用しています。
各項目の `source.url` / `japaneseDefinitionSource.url` は元の記事へのリンクです。
著者と編集履歴は、その記事の「履歴」から確認できます。
利用条件は [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.ja) です。

抽出には [Kaikki.orgの日本語版Wiktionaryデータ](https://kaikki.org/jawiktionary/rawdata.html)
（2026-11-01ダンプ、2026-11-02抽出、Wiktextract）を使用しました。
原本のSHA-256と取得URLは `sources.json` に保存しています。

原文を利用した定義は、空白・句読点・半角カンマを整形しています。
別読みの語義、同音の別表記、参照先だけを示す説明などは、そのまま継承しません。
誤った取り違えや説明不足が見つかったものは、英語原文や追加資料と照合して独自に編集しました。
独自編集の文章は `definitionIndividuallyEdited: true` として区別します。

## 見出し・読み・語義の照合

[JMdict / EDRDG](https://www.edrdg.org/jmdict/j_jmdict.html)
2026-10-05版（jmdict-simplified 3.6.2）を使用しています。
見出し・読み・語義の適用先と、元の項目IDを各採用記録に保存します。
[EDRDGの利用条件](https://www.edrdg.org/edrdg/licence.html)（CC BY-SA 4.0）を適用します。
原本取得記録は `../../general10000/source-metadata.json` です。

追加の確認資料は `supplementary-sources.json` に保存しています。
これらの資料は事実・用法の確認に使用し、その説明文を転載していません。
固有名詞について、ロゴ、肖像、歌詞、音声、公式画像は追加していません。

## 確認範囲

全件の読み・表記・採否・出典を台帳で照合し、説明の書式や参照関係を検査します。
一部は個別編集、一部は日本語辞書の定義の継承です。
全件の専門家校閲や、児童の学年への個別認定を終えたという意味ではありません。
採用語は暫定レベル4に置き、画像なしの説明として登録します。
難しいこと自体は除外理由にしません。
