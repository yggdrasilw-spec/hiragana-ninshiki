# しりとり75注文の修正記録

元注文: [単語・意味・画像の修正依頼](shiritori-word-meaning-image-corrections.md)。IDは修正前CSVの行番号。統合後の行番号との対応は `data/corrections/2026-10-12-word-image-ledger.json` の `currentBeforeIds` に保存する。

意味17語を修正し、蛙→カエル、鹿→シカ、茄子（なすび）→ナスの3組を統合。難易度・検索語・対象外の項目は維持する。「帰る」は別の語義なので残す。なすびは同じ野菜の別名として統合したため、独立したゲーム項目は削除する。

画像注文のうち、ヤギの注文は「家畜に限らない」という意味への指摘として扱い、意味を追加修正して画像を維持する。合計18語の意味を修正する。画像54枚は、27枚を元シートから切り出し直し、27枚を再生成する。机は元シートでも脚が欠けていたため再生成する。

切り出し範囲は `data/image-coverage/2026-10-12/word-image-crop-repairs.json` に記録し、`scripts/recrop-shiritori-reviewed-assets.py` で再現できる。再生成シート、プロンプト、切り出し範囲、最終目視確認はmanifestと生成計画に保存する。画像を共有する全CSV行とmanifestのaliasesを照合する。統合で使われなくなった画像はmanifestから除き、元PNGは履歴資料として残す。

ユーザーが未確認とした単語・読み・意味・画像を一括で確認済みにしない。今回の変更項目を coverage の `wordImage75Review` に個別記録し、元のユーザー判定は注文原文を保持する。画像は生成プロンプトだけで合格とせず、最終256px画像を目視点検する。

語義・構造の確認資料:

- [環境省：アメリカザリガニ](https://www.env.go.jp/nature/intro/2outline/attention/amezari.html)：条件付特定外来生物。ザリガニ全体を外来生物とせず、飼育個体を野外へ放さない説明を加えた。
- [日本大百科全書：ドレス](https://kotobank.jp/word/%E3%81%A9%E3%82%8C%E3%81%99-3161697)：形による分類にワンピース・ツーピースがあり、上下がつながる服に限定しない。
- [ヤマハ：リコーダーの音程](https://www.yamaha.com/ja/musical_instrument_guide/recorder/mechanism/mechanism002.html)：下部の2位置はダブルホール。単孔5つ・二重孔2組が見える正面画像にした。
- [国立環境研究所：ナマズ](https://www.nies.go.jp/biodiversity/invasive/DB/detail/50800.html)：成体は上下のあごに1対ずつ、計4本のひげを持つ。生成画像の余分な下あごのひげを再修正した。
- [ヤマハ：クラリネット各部の名称](https://www.yamaha.com/ja/musical_instrument_guide/clarinet/mechanism/)：マウスピース、バレル、上下管、ベルを持つ構造を確認した。

サイコロは同じ面の目が重複しない、上3・前1・右2の一個に変更する。一般的なサイコロの対面は合計7なので、2と4が同時に見えること自体は誤りではない。注文の意図に沿って、面の対応が明確な画像にする。

適用は `python scripts/apply-shiritori-word-image75.py`。CSVの前後SHA256と変更前の全行を既存のdictionary-imports履歴へ追記し、過去のレビューを復元可能にする。最後に `python scripts/build-shiritori-review-updates.py` を実行し、更新順と画像指紋を再構築する。

検証: `python tests/shiritori-word-image75.py`、全画像coverage監査、辞書データ・import履歴・意味レビュー・round2・review93の既存テストを実行。Chromiumで画像確認画面のPC/スマートフォン表示、更新順、画像キャッシュ更新、古い確認データの無効化を検証。既存の画像確認テストは凍結計画の旧行IDを参照していたため、画像ファイルから現在の行を解決するよう修正した。

最終画像一覧: `data/image-coverage/2026-10-12/word-image75-final.jpg`。変更後は6,547行・1,992参照画像で、未参照manifest・破損参照・coverageの語義ずれはいずれもない。
