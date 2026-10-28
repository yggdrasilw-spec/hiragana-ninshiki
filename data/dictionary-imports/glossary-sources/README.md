# 用語集相当の語彙の資料

`ipsj-wordlist.csv` は、情報処理学会 情報入試委員会が公開した「情報科全教科書用語リスト第2版」（2026年10月13日更新）のCSV出力。2026年10月28日に取得した。

- 公開ページ: https://sites.google.com/a.ipsj.or.jp/ipsjjn/resources/wordlist-v2
- 元の表: https://docs.google.com/spreadsheets/d/1FYsq1-ZmwrovR1j8_Q_M5QmSlj6NIZdy/view
- 著作者表示: 情報処理学会 情報入試委員会
- ライセンス: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

元のCSVのバイト列を保持し、SHA-256を本バッチの `sources.json` に記録。採用語と説明の派生データもCC BY-SA 4.0で提供する。説明の改行を空白へ、半角カンマを読点へ変え、注番号を除き、必要に応じ句点を補った。説明がなく意味を確定できない語、読みが確定できない語、コード構文などは自動追加しない。

`ipsj-selected.json` は読みを特定できた掲載語の選定記録。実際の登録は本バッチの `review.json` と `excluded.json` により、既存語と手作業で説明を用意した語を優先する。`ipsj-held.json` と `ipsj-deferred.json` は読み・説明・収録範囲の確認を残したもの。保留語を登録済みとは扱わない。

JMdictは語形と読みの照合に利用。James William BREEN / Electronic Dictionary Research and Development Group、CC BY-SA 4.0。バージョンとSHA-256は本バッチの `sources.json`。原辞書の英語の語義は転載しない。

倫理・古典および手作業の情報用語の説明は独自作成。市販の用語集から本文・索引を複製していない。用語集の公開目次、学習指導要領、教科用資料などで分野を確認し、哲学・心理学・宗教・文学の標準的な語義を編集した。全語を一次文献で一件ずつ照合したものではない。
