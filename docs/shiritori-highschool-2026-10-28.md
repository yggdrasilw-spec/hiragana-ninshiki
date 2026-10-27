# 高校倫理・情報・古典の語彙追加（2026-10-28）

既存21,355行をバイト単位で保持し、228項目を末尾へ追加。合計21,583項目、新しい読みは222種類。

|分野|追加数|例|
|---|---:|---|
|倫理|66|無知の知・イデア・定言命法・功利主義・ケアの倫理|
|情報|80|量子化・二分探索・主キー・多要素認証・箱ひげ図|
|古典|82|係り結び・已然形・再読文字・をかし・らうたし|

全項目を意味別レベル5「はってん」に配置。CSVの旧3段階列は3。画像は制作せず `image_mode=none` とし、外部画像検索もしない。追加履歴、意味別難易度、画像確認カタログ、更新順を同期した。

既存の同表記12語は再追加しない。同じ読みでも別の意味を持つ「現在／原罪」「ジン／仁」「お菓子／をかし」「糸・ito／いと」「驚く／おどろく」「罵る／ののしる」は別義として追加し、その理由を記録した。「ん」終わり18項目も収録し、通常の負け判定は維持する。

古語は歴史的な表示綴りと現代の発音による読みを分ける。例は「あはれ→あわれ」「らうたし→ろうたし」「やむごとなし→やんごとなし」「参づ→もうず」。活用する古語も辞書形で登録する。古語の全用例や全語義を網羅する辞書ではない。

## 出典と編集確認

- [神戸高専の倫理シラバス](https://www.kobe-kosen.ac.jp/education/syllabus/2026/html/C2_1011020.html)と[広島県の倫理問題](https://www.pref.hiroshima.lg.jp/uploaded/attachment/215003.pdf)を科目範囲や用語の参考にした。
- [文部科学省の情報科関係資料](https://www.mext.go.jp/a_menu/shotou/zyouhou/detail/mext_01831.html)、情報Ⅰ教員研修用教材の[第2章](https://www.mext.go.jp/content/20200928-mxt_jogai01-100013300_001.pdf)・[第4章と巻末](https://www.mext.go.jp/content/20200722-mxt_jogai02-100013300_006.pdf)、[IPAの用語例集](https://www.ipa.go.jp/shiken/asia/qv6pgp0000002s9q-att/000027072.pdf)を参考にした。
- [文部科学省の国語編解説](https://www.mext.go.jp/content/20250410-mxt_kyoiku01-100002620_02.pdf)、[三省堂の古典文法項目](https://tbqr.sanseido-publ.co.jp/09-seisenkoten/contents/koten-bunpo-list/)、[河原学園の古典文法シラバス](https://irweb.kawahara.ac.jp/uhe_syllabus/SyllabusDetail.aspx?jc=COM30001&jn=2022)、[小学館の「あはれ」](https://japanknowledge.com/introduction/keyword.html?i=1796)を参考にした。取得できないページでは検索インデックスの公開抜粋を参照した。
- 既存JMdict索引で15項目の表記と読みの一致を確認した。残り213項目は科目の標準用語や古語として編集確認したもので、独立した辞書見出しをすべて照合したものではない。説明は独自の短文であり、教材や辞書の定義・例文を転載していない。

候補、既存語による除外、各語の語義・年齢・同音異義語の判断、参考資料、件数は `data/dictionary-imports/2026-10-28-highschool.*` に保存。

## 検証

- `tests/shiritori-highschool.py`：既存21,355行のバイト単位保持、228項目のID・読み・語義・難易度・画像モード・台帳対応、古語の現代読みを確認。
- `tests/shiritori-highschool-browser.cjs`：PC 1280px・スマホ390pxで全228語の説明・画像なし表示・横はみ出し・レベル別候補数を確認。6種類の同音異義語の切替、各画面10語の実入力、カタカナ入力、「ん」終わりの負け判定を確認。
- 既存の辞書データ・取り込み履歴・レビューゲート・意味別難易度の回帰検査が合格。

検証結果は `data/dictionary-imports/2026-10-28-highschool.validation.json`。画面記録はローカルの `qa-output/highschool/`。公開サイトの反映確認は含まない。
