# しりとりアプリへの接続

既定候補：`C:/Users/user/hiragana-ninshiki`。異なる作業場所やブランチをユーザーが指定した場合はそちらを優先する。現在のファイル・Git状態を確認する。

- 辞書：`whitelist.csv`。`reading,word,meaning,...,image_asset,image_mode,image_credit`。語IDはヘッダーを除く1-based行番号。語義の違う同音語を混同しない。
- 保存画像：`assets/shiritori/`、元シート：`assets/shiritori/sheets/`。
- 登録：`scripts/import-shiritori-assets.py`。登録バッチは `data/batches/`。
- 由来・プロンプト・共有先：`assets/shiritori/manifest.json`。
- 全語確認：`data/image-coverage/review-2026-10-10.json`。行IDと語義・画像を辞書へ同期する。
- 修正・取り込みの履歴：`data/dictionary-imports/history.json`。新しい画像割り当ても記録し、ハッシュと復元可能な前後行を維持する。Windows改行差は必要に応じてUTF-8テキストをLFに正規化して照合する。
- 画像確認画面の更新日時・ハッシュ：`scripts/build-shiritori-review-updates.py` で再作成。

登録CSVの必須列：`id,reading,word,meaning,filename,scene,sourceSheet,tileIndex,generatedAt,prompt,cropValidation`。`sourceSheet` は `sheets/` からの相対パス。`cropValidation` はリポジトリ内の検証JSONへの相対パス。語義・ID・出力名・コマ番号が計画・元シート・検証記録と一致していることを登録前に確認する。現在のインポーターは記録を再計算し、出力ファイル名の末尾 `-word-ID.png` も確認する。

新しいチェック方式をまだ持たない作業コピーでは、同梱切り出しスクリプトの `verify_report` を組み込むか、登録直前に同関数で全16枚を再検証する。古い目視余白・等分切り出しの実装へ戻さない。

最低限の確認：

```powershell
python -B scripts/crop-shiritori-grid.py --help
node tests/shiritori-data.cjs
node tests/shiritori-import-history.cjs
python -X utf8 scripts/audit-shiritori-image-coverage.py
```

今回のバッチの語ID一覧でブラウザー確認を行う。既存の `tests/shiritori-wave6-browser.cjs` は追加52語をPCとスマホ、外部検索なしでゲーム・画像確認画面に表示する例。別バッチでは現在のID・語義・クレジットを使う。実行環境に合わせて `PLAYWRIGHT_MODULE` と `QA_EXECUTABLE` を指定する。

既存画像の品質候補が残っている場合、今回追加した画像の自動検証結果と区別する。全既存画像の意味まで確認したと報告しない。
