# 一般語・別表記の大量追加（2026-10-29）

「力」のような基本語の不足を補い、一般名詞・抽象語・別表記を **20,611項目** 追加した。ユーザーの追加指示に従い、別表記も収録対象とし、1万項目を上限にしなかった。読みだけで既存語を除くと芸人名「ちから」のために普通の「力」まで除かれるので、読みと表記の組で既存語を照合した。

|項目|件数|
|---|---:|
|今回の追加|20,611|
|新たに登録された読み|16,494|
|既存の読みへの追加がある読み|2,221|
|新規項目内に複数表記がある読み|1,392|
|基本語として個別に説明を編集|112|
|個別編集分の意味別レベル1 / 2 / 3|27 / 47 / 38|
|資料由来の説明を使う意味別レベル4|20,499|
|「ん」で終わる追加項目|3,210|
|画像|全件が説明のみ|

登録前66,912項目をバイト単位で保持し、今回登録直後は87,523項目。別作業のGASログ106項目がその後追記され、最終確認時の通常辞書は87,629項目・79,906読み。読みが同じ表記はゲームで一つの語にまとまり、意味や表記を切り替えて表示する。別表記で既出判定を回避する変更はしていない。

## 出典と選定

- 日本語WordNet **2.1**: https://bond-lab.github.io/wnja/jpn/downloads.html
- JMdict（EDRDG）2026-10-05版 / jmdict-simplified: https://www.edrdg.org/jmdict/j_jmdict.html
- OMW English WordNet **2.0**（WordNet 3.0）: https://github.com/omwn/omw-data/releases/tag/v2.0

WordNetの名詞を候補にし、JMdictの同一表記・読み・名詞語義と照合する。さらにJMdictの英語語義と英語WordNet見出しが正規化後に完全一致する語義を採る。低確度の語義、古語・廃語・稀語等のタグ、既存の禁止語、原資料の明白な誤記候補、地域限定・循環説明などを除く。26,725候補から語義照合で20,923項目に絞り、329項目を説明の個別編集待ちとして保留。基本語の補完と編集を反映して20,611項目になった。

**自動照合は語義の正しさを証明するものではなく、20,611項目すべての人手校閲は行っていない。** 資料由来の日本語説明には訳文の硬さや原資料の誤りが残る可能性がある。児童向けに個別編集した112項目を除き、CPU用の意味別レベルは4に置く。児童自身は全レベルで入力できる。WordNetの長文を機械的に断片化せず、採用した定義文を句点・空白の整形にとどめて保持する。

「力」「声」「形」「様子」「物」「子供」「階段」「月曜日」などには独自の短い説明を作成した。独自説明に元のWordNet語義IDを出典として付けないよう区別し、候補段階のIDは監査用の別欄に保存する。

原資料のURL・取得日・SHA-256は `data/general10000/source-metadata.json`。WordNetの許諾文・著作権表示は `wordnet-LICENSE.txt`、英語資料は `english-wordnet-LICENSE.txt`、JMdictは `jmdict-NOTICE.md`。設定の「一般語・別表記データの出典」と、各語の説明欄から出典を開ける。JMdict由来の抽出情報にはCC BY-SA 4.0が適用され、日本語WordNetには同梱のWordNet Licenseが適用される。

## 管理と更新

- `data/general10000/entries.jsonl`: 採用語・原資料ID・照合した英語・編集区分・レベル・出典。
- `data/general10000/editorial.tsv`: 個別説明の編集原稿。既存語や出典照合が通らなかった候補も含むため、このファイル自体の行数は追加数ではない。
- `data/general10000/catalog.sqlite`: 読みと表記の索引、説明のFTS5検索。ゲームはDB全体をダウンロードしない。
- `data/general10000/selection-deferrals.json`: 説明の個別編集待ち。
- `data/dictionary-imports/2026-10-29-general10000.*`: CSV、採用記録、登録前後のハッシュ・件数。

SQLiteの使用例:

```sql
SELECT reading, word, meaning FROM entries WHERE reading = 'ちから';
SELECT reading, group_concat(word, ' / ') FROM entries
GROUP BY reading HAVING count(*) > 1;
SELECT word, reading, meaning FROM entries
WHERE id IN (SELECT rowid FROM search WHERE search MATCH 'トレーニング');
```

原資料の大容量ダウンロードはGitに含めず、採用記録と許諾文を保存する。原資料はメタデータ内のURLから `sources/` に取得し、SHA-256を照合して展開する。候補の再現は `python -X utf8 scripts/prepare-shiritori-general10000.py`。既存の登録記録がある場合は登録前の66,912行を使い、後続追加に影響されない。取り込みは `import-shiritori-general10000.py` の既存ゲートを利用し、履歴・難易度・画像台帳を同期する。登録済みバッチの再実行は追記しない。

通常の配信再生成は `node scripts/build-shiritori-delivery.cjs`。本文と出典は最大128読みのJSONで必要時に取得し、読み索引だけを起動時に取得する。地名パックも現在の通常辞書のハッシュに合わせて再生成する。

## 検証

- `node tests/shiritori-general10000.cjs`: 全追加項目の配信、出典、難易度、画像なし、英語見出し照合の記録、既存行保持、別表記と「力」の通常語義、追加履歴。
- `node scripts/build-shiritori-delivery.cjs --check`: 現在のCSV・難易度・出典メタデータと配信物の一致。
- `node tests/shiritori-delivery.cjs`: 全意味・読みと125条件の候補数、分割取得、失敗後の再試行、キャッシュ。
- `node tests/shiritori-geography.cjs`: 日本の地名・駅名パックとの統合、ハッシュ・重複・集計。
- `node tests/shiritori-delivery-browser.cjs`: PCとスマホで通常語「力」の低学年説明、出典、実入力とCPUの応答、レベル4の「政党」、設定の利用条件リンク、既存の通信再試行とリセット競合。
- SQLite `PRAGMA integrity_check`、87,629項目の難易度・画像確認台帳・更新履歴の件数とハッシュ一致を確認。

公開サイトへの反映はこの作業では行っていない。
