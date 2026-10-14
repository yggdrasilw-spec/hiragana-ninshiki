# 画像の優先設定・起動時注意・誤り報告（2026-10-14）

## 利用者の操作

設定の「画像のえらびかた」で全体の既定を選び、動物、植物・果物・野菜、菌類、自然・地理、その他で上書きできます。初期値は保存済み画像優先です。動物などをWikimedia優先にすれば、CSVにAI生成画像が登録されていても検索します。設定は端末に保存されます。

画像が見つからないときは保存済み画像を使い、代替画像であることを表示します。Wikimediaは写真に限らず図も返します。検索結果が語を正しく表すかの独立検証はしていません。作者・利用条件・出典のリンクを表示し、CC BY / CC BY-SAで作者とライセンスURLを確認できるもの、またはパブリックドメイン相当と確認できるものを採用します。

分野は `shiritori-image-policy.js` で各行の語・説明・検索語から自動判定します。「かき」の柿・牡蠣・書きなどは別々に判定します。架空のキャラクターを動物扱いすることを避けています。分類は完全ではなく、画像の分野についてもフォームから報告できます。CSVや画像マニフェストの既存形式は変更していません。

起動するたびに、説明・画像にAI由来の不正確さがあること、文字入力の楽しい練習が主眼であることを表示します。設定から再表示できます。

報告フォームは注意書き、設定、語の詳細から開けます。詳細から開いた場合は、選択中の語義・読み・表示画像URL・画像クレジットを添付します。名前やメールアドレスの入力欄はありません。

## Firebase運用

- 専用プロジェクト: `shiritori-feedback-20261014`（Shiritori Feedback）
- [報告一覧を管理するFirestoreコンソール](https://console.firebase.google.com/project/shiritori-feedback-20261014/firestore/databases/-default-/data/~2Freports)
- 保存先: Cloud Firestore `(default)` / `reports/{UUID}`
- 実際のリージョン: `nam5`。CLIの初期デプロイが既定リージョンでデータベースを作成しました。
- 認証: 匿名Firebase Authentication。メール・氏名は取得しません。再送受付の照合用に匿名UIDを保存します。
- ルール: `firebase-feedback/firestore.rules`。投稿者がIDを指定した自分の報告の受付確認だけを許可。一般クライアントの一覧取得、他人の報告取得、更新、削除は禁止。管理者はFirebaseコンソールから確認できます。
- 入力の型・長さ・許容キーを検証。報告と投稿制限レコードを原子的に保存し、同じ匿名UIDから30秒以内の連続投稿を拒否します。これは完全なスパム防止ではありません。新規匿名UIDを大量に作る攻撃には別途App Check等が必要です。
- Webの公開設定は `shiritori-feedback-config.js`。管理者の秘密鍵を配信しません。Firebase SDK 12.4.0を報告送信時にだけ読み込みます。
- 未送信報告は `shiri-feedback-pending-v1` に最大30件保存。失敗時は未送信と表示し、設定のボタンから明示的に再送します。自動送信はしません。送信確認の待機は15秒で打ち切り、バックグラウンドで確認できた報告は待機終了後でも待ち行列から除去します。
- 一度受付済みのUUIDは再送前に確認し、応答が失われた場合も二重登録しません。複数の未送信報告を再送すると、30秒制限により残りが未送信になる場合があります。時間を置いて再送します。
- サイトデータを消すと未送信報告も失われます。

ルール・認証設定のデプロイ:

```powershell
cd C:\Users\user\hiragana-ninshiki\firebase-feedback
firebase deploy --only firestore:rules,auth --project shiritori-feedback-20261014
```

この設定にHostingは含まれません。アプリ本体の公開は従来のGitHub Pagesの公開手順を使います。

## 検証

- `node tests/shiritori-image-policy.cjs`: 分野と同音異義語、継承、保存済み画像で検索しないこと、Wikimediaで保存済み画像の優先を覆せること、切替時のキャッシュ、検索失敗時の代替表記。
- `node tests/shiritori-data.cjs` / `node tests/shiritori-meaning.cjs`: 既存辞書・画像系統・説明動作。
- `tests/shiritori-feedback-browser.cjs`: Edgeで1280px / 390px、起動注意、設定保存、出典リンク、語義の添付、未送信保存、横はみ出しを検証。`QA_LIVE_REPORT=1` では実FirebaseへのSDKによる再送も検証。
- `node tests/shiritori-feedback-live.cjs`: 実Firebaseへの原子的な保存と、自分の受付確認、他者/未認証の閲覧・一覧取得・改ざん・削除・不正UID・不正入力・連続投稿が拒否されることを検証。テスト報告は「接続確認（テスト）」として保存されます。

ブラウザー試験ではWikimediaの応答は固定フィクスチャです。実際の全語の検索結果や写真の正しさを確認した試験ではありません。
