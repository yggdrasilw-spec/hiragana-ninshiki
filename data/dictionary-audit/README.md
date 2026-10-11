# 外部辞書との照合

JMdict（James William BREEN / Electronic Dictionary Research and Development Group）を使用。
原データと、このディレクトリの派生データ（候補一覧・照合結果）は **CC BY-SA 4.0**。
表記・読み・項目ID・選択用の属性を抽出し、語義・訳語・例文は複製していない。
加工内容は読みのひらがな化、既存データとの比較、候補の絞り込み。

- [辞書とドキュメント](https://www.edrdg.org/wiki/index.php/JMdict-EDICT_Dictionary_Project)
- [EDRDG の利用条件](https://www.edrdg.org/edrdg/licence.html)
- [CC BY-SA 4.0 のライセンス全文](https://creativecommons.org/licenses/by-sa/4.0/legalcode)
- [JSON変換元](https://github.com/scriptin/jmdict-simplified)

2026-10-11の結果は、日常・学校生活の24語追加後の6,144行が対象。辞書は2026-10-05版の完全版。
`summary.json` に版・取得先・辞書JSONとCSVのSHA256を記録。
`candidates.csv` は未レビューの作業用一覧。アプリには直接読み込ませない。
同じ項目の別表記・異なる読みもあるため、行数を追加できる語数とみなさない。

再実行:

```sh
python scripts/audit-shiritori-dictionary.py /tmp/jmdict-eng-3.6.2.json \
  --output /tmp/shiritori-dictionary-audit \
  --source-url 'https://github.com/scriptin/jmdict-simplified/releases/tag/3.6.2%2B20261005200550'
```

定期更新時は最新の完全版JSONを作業領域へ取得して再照合し、採用済みの項目も読み・表記を再確認する。
辞書未収録は誤りと断定しない。辞書の読みとの不一致は、略記・単位・固有名詞・別語義も含むため自動修正しない。
候補はcommon属性を持つ現代の名詞を中心に、読みと語義の適用先を守って抽出。
語義の注意タグだけでは年齢適合を保証できない。説明、年齢、同音異義語、画像は個別に確認する。
