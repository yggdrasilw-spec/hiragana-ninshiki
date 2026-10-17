# しりとり画像のR2配信

ゲームと画像点検ページは、固定した配信先 `https://shiritori-images.yggdrasil-learning.workers.dev` を使います。アプリ自体の公開先はGitHub Pagesです。辞書CSV、画像manifest、画像の出典・権利表記、生成プロンプト、切り出し検証記録はGitに残します。

## 保管先

| バケット | 内容 | 公開範囲 |
| --- | --- | --- |
| `shiritori-images` | 単語画像と `shiritori_title.png` | 読み取り専用Workerから配信 |
| `shiritori-image-archive` | 生成元シート、過去の修正版、点検用画像 | 非公開 |

公開WorkerはGET・HEAD・OPTIONSだけを受け付けます。画像パスは単語画像とタイトルだけに限定し、バケット一覧・生成元シート・更新APIは公開しません。ブラウザー用CORS、ETag、Content-Type、5分の再検証付きキャッシュを返します。

画像ファイルは `.gitignore` 対象です。既存のローカル画像はそのまま使えます。Gitの画像削除はローカル原本の削除を意味しません。

## 新しくcloneした場合

公開画像は認証なしで復元できます。存在するファイルは上書きしません。

```powershell
node scripts/restore-shiritori-r2.cjs
```

全画像のパス・容量・SHA-256・保管バケットは `data/image-coverage/r2-assets.json` に記録しています。非公開の生成元も復元する場合は、対象2バケットに限定したR2 S3認証情報をリポジトリ外のJSONファイルに保存して指定します。

```powershell
npm install --prefix cloudflare/images
node scripts/restore-shiritori-r2.cjs --include-archive --s3-credentials C:/private/r2-credentials.json
```

認証JSONのキーは `accessKeyId` と `secretAccessKey` です。チャット・ソースコード・Gitには保存しません。

## 画像の追加・修正

従来どおり画像生成・切り出し・manifest登録・辞書の整合性検証を行い、画像更新記録を作ります。Gitから画像履歴を外した後も、保存済みSHA-256と比較して変更日時を維持します。

```powershell
python scripts/build-shiritori-review-updates.py
python scripts/shiritori-r2-inventory.py --output data/image-coverage/r2-assets.json
```

少量の差分転送では公式CLIのOAuth認証を使えます。認証値はCLIからプロセス内だけに読み込み、表示やファイル出力はしません。

```powershell
npm install --prefix cloudflare/images
node cloudflare/images/node_modules/wrangler/bin/wrangler.js login --scopes account:read user:read workers:write
node scripts/sync-shiritori-r2.cjs --wrangler cloudflare/images/node_modules/wrangler/bin/wrangler.js
```

大量転送には、2バケット限定・短い有効期間のS3認証を使います。

```powershell
node scripts/sync-shiritori-r2.cjs --s3-credentials C:/private/r2-credentials.json --concurrency 8
```

転送ごとに実データを読み戻してSHA-256と容量を照合します。進行記録はGit対象外の `qa-output/r2-transfer.jsonl` に保存し、中断時は未検証分だけ再開します。再点検するときは `--verify-only` を指定します。転送後に辞書・manifest・更新記録・画像一覧をコミットしてください。R2上の不要ファイルを自動削除する操作は含めていません。

## Workerの確認・更新

WorkerをCLIから更新するときは `workers_scripts:write` も付けてログインしてください。画像の差分転送だけではこの権限は不要です。

```powershell
node cloudflare/images/node_modules/wrangler/bin/wrangler.js login --scopes account:read user:read workers:write workers_scripts:write
npm --prefix cloudflare/images run check
npm --prefix cloudflare/images run deploy
node tests/shiritori-r2.cjs
node tests/shiritori-r2-browser.cjs
```

`tests/shiritori-r2-browser.cjs` はローカル画像配信を禁止し、実際のWorkers配信でゲームを3往復、画像表示、リセット、画像点検ページをデスクトップ・スマートフォンで確認します。`QA_APP_ORIGIN` をGitHub Pagesのアプリorigin（末尾スラッシュなし）に設定すると公開版も確認できます。

既存のオフライン用ブラウザーテストでは `tests/shiritori-r2-fixture.cjs` で固定配信先をローカル原本に置き換えます。実配信テストとは分けてあります。

## 履歴整理

画像の転送・読み戻し検証・ゲーム確認後に、画像拡張子だけを全履歴から除外します。コード・CSV・出典・生成記録の内容とコミットの親子関係は維持しますが、Gitの仕様によりコミットIDは変わります。旧IDと新IDの対応は移行時の記録を参照します。

他の端末や古い作業ブランチから旧履歴をmerge/pushすると画像が再び入るため、更新後は新しいcloneを使ってください。ローカルの未コミット作業を残す場合は別途保全してから移してください。GitHub内部の到達不能オブジェクトやPR用参照の整理はGitHub側の処理に依存します。
