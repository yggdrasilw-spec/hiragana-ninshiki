# 理科4分野の大量収録

化学 1,512・物理 1,078・生物 2,298・地学 1,323の **6,211語義**を追加。従来の33,655行をそのまま保持し、通常辞書は39,866行になった。約6,400件の最初の候補に、高校の主要単元の不足語を補足した。件数で打ち切らず、既存語・表記違い・専門語義未確認の候補を整理した結果の件数である。

## ゲームでの利用

- 追加語は意味別レベル5「はってん」。低いレベルのCPUやヒントには混ぜない。子どもの既知語入力は従来どおり認める。
- CPUのジャンルに「化学」「物理」「生物」「地学」を追加。保存済みの選択は維持するため、必要に応じてチェックするか「すべて選ぶ」を選ぶ。
- 画像は説明のみ。外部画像検索をせず、各語の説明に出典を表示する。設定にも原資料とライセンスへのリンクを置く。
- 説明は従来の最大128読みの分割JSONで必要時に取得する。管理用CSV・SQLite・原資料は起動時に配信しない。

## 大学受験との対応と確認の限界

[高等学校学習指導要領解説・理科編](https://www.mext.go.jp/content/20250311-mxt_kyoiku02-100002620_05.pdf)の単元構成を参考に、力学・熱・波動・電磁気・原子、物質の構成・理論・無機・有機・高分子、細胞・代謝・遺伝・発生・恒常性・生態・進化、地球内部・岩石地史・気象海洋・天体宇宙のチェックリストを作成した。

`core-coverage.json` は **958項目**の登録照合で、未登録0件。科目間の共通語を含むため、これは異なる単語の総数ではない。全国の全教科書・全大学の出題語を照合した完全網羅の証明ではない。大学範囲を超える発展語も含む。

説明は独自編集 474件、Wiktionary直接抽出 795件、Tomoshi由来 4,942件。TomoshiにはJMdictの英語語義からAI補助で作成され別モデルでレビューされた説明が含まれ、原配布元も全件人手校閲済みとはしていない。自動照合・サンプル点検・重要語の編集修正は、全6千語を専門家が人手校閲したこととは区別する。

同音異義語の取り違え、古い定義、主語の曖昧さを点検し、「仕事」「核」「細胞膜」「同化」「硝化」「基質」「分散」「摂動」「レプトン」「クーロンの法則」「太陽日」などを編集修正。「卵割」の科学用語の読みは「らんかつ」とし、「かいわり」の別語義を混ぜない。

## 管理・出典

- `data/dictionary-imports/2026-10-28-science.*`: 登録バッチ・語義別根拠・除外理由・件数・前後SHA-256。
- `data/science/entries.jsonl`: 表記・読み・意味が完全一致する場合だけ科目と出典を結び付ける配信メタデータ。
- `data/science/catalog.sqlite`: 読み・表記・科目の索引と全文検索を持つ管理用データベース。`entries` 表と `search` FTS表を持つ。
- `data/science/core-topics.txt` / `core-coverage.json`: 単元別の登録チェックリスト。
- `data/science/editorial-definitions.tsv`: 読みと説明の編集修正。
- `data/science/lexical-evidence.jsonl` / `source-metadata.json`: JMdict ID・英語語義・分野と利用資料の版・取得データSHA-256。

見出し・読みは [JMdict / EDRDG](https://www.edrdg.org/jmdict/j_jmdict.html) を使用。James William Breen および Electronic Dictionary Research and Development Group の辞書を利用条件に従って抽出・整理した。利用条件：[EDRDG licence](https://www.edrdg.org/edrdg/licence.html)、[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。

日本語の語義は [Wiktionary執筆者](https://ja.wiktionary.org/)（[Kaikki / Wiktextract](https://kaikki.org/)経由）および [Tomoshi (Y1Z) 公開データ2026-09-02版](https://huggingface.co/datasets/yuany1z/tomoshi-dict-data)から抽出・短縮・修正。これらに由来する追加辞書データはCC BY-SA 4.0で提供する。権利表記と加工の説明は `tomoshi-NOTICE.md` と `tomoshi-LICENSE.md` も参照。取得した上流DBや画像・筆順資料は同梱しない。

除外・保留の内訳：

- 日本語の専門語義を自動照合できず・要編集：486件
- 既存の同じ読み・表記または別表記：277件
- 専門語義と分野の対応を再確認するため保留：1件
- 同じ表記の別の読み・別語義。専門語の読みと一致しない：5件
- 同じJMdict見出し・同じ読みの表記違いを統合：5件
- 同じ読み・同じ説明の表記違いを統合：2件

## 更新と検証

配信再生成は `python scripts/build-shiritori-grade-bands.py`。管理DB再生成は `python scripts/build-shiritori-science-catalog.py`。CSVの語義を変更する際は、難易度・履歴・画像確認台帳と `entries.jsonl` の完全一致キーも更新する。不一致のメタデータは配信ビルダーが停止する。

検証コマンド：

```
python tests/shiritori-science.py
node tests/shiritori-delivery.cjs
node scripts/build-shiritori-delivery.cjs --check
node tests/shiritori-science-browser.cjs
```

ブラウザ検証はPC幅1280px・スマホ幅390pxで全追加語の表記・説明・意味別難易度・科目・出典・説明のみ表示・横はみ出しと、4語の実入力を確認する。これは語義の科学的正確性を全件証明するテストではない。

最終検証：上記4コマンドは合格。PC・スマホ各6,211語の表示と出典、4ジャンルの難易度、各4語の入力を確認。検証記録は `data/dictionary-imports/2026-10-28-science.validation.json`、画面例は `qa-output/science/`。
