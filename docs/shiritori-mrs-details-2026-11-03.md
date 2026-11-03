# ミセス関連語彙の補足情報

既存の207語義に、人物・バンドの活動歴、作品の発売日・収録アルバム・収録位置、公演の日程・会場を追記。
大森元貴のソロ作品、同名の楽曲・アルバム・公演を含む。一般語の「ミセス」は対象外。

`shiritori-mrs-details.js` の補足は読み・表記・既存の説明の完全一致で対応する。
元のCSV、語義ID、難易度、画像設定を維持し、通常の分割配信とCSV経由の読み込みの両方へ補足と出典を付ける。
説明画面の既存の詳細領域に表示し、「くわしく きく」で読み上げる。
配信生成時に207語義すべての対応を検証し、辞書編集で対応が失われた場合はエラーにする。

2026-11-03に公式ディスコグラフィ・プロフィールとUniversal Musicの作品情報を確認。
発売日はその盤の発売日を扱い、ANTENNAは2026年のアナログ再発と区別して2023年7月5日の通常盤を採用。
曲の収録先には可能な範囲でオリジナルのスタジオアルバムを優先。
公演36語義は、初期の自主公演も掲載するEnchanted Tomeの公演年表を参照し、公式情報と混同しない出典名を表示する。
公演名を再使用したものは年表の最初と最後の日程を示すため、連続した一つのツアー期間を意味しない。
将来の掲載日程は実施済みとして扱わない。

- [公式ディスコグラフィ](https://mrsgreenapple.com/discography/)
- [公式プロフィール](https://mrsgreenapple.com/feature/profile)
- [ANTENNA 通常盤](https://mrsgreenapple.com/discography/detail/162/)
- [大森元貴 OITOMA](https://www.universal-music.co.jp/ohmori-motoki/products/uu1aa-01054/)
- [Enchanted Tome 公演年表](https://enchantedtome.net/live-list)

検証成功: `node tests/shiritori-mrs-details.cjs`、`node tests/shiritori-delivery.cjs`、`node tests/shiritori-image-policy.cjs`、`node scripts/build-shiritori-delivery.cjs --check`。
ブラウザ検証は1280px・390px・320px幅で詳細・出典・同名語の切り替え・読み上げ用テキスト・外部画像検索なしを確認。
既存の `shiritori-meaning.cjs` はモックの `dictionary` 未定義、`shiritori-entertainment.cjs` は過去の辞書ハッシュ不一致で失敗する。
両方とも変更前の本体で同じ失敗を再現。今回の変更では元のCSVを変更しない。
