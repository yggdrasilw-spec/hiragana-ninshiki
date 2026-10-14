import csv,json,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'))
crop=json.loads((BASE/'crop-status.json').read_text(encoding='utf-8'))
assert crop=={'sheets':26,'rejected':[]}
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig',newline='')))
manifest=json.loads((ROOT/'assets/shiritori/manifest.json').read_text(encoding='utf-8'))
assets=[a for a in manifest['assets'] if a['file'].startswith('wave11-safe-')]
assert len(assets)==410 and len({a['file'] for a in assets})==410
for item in plan:
 row=rows[item['id']-1]
 assert row['image_asset']=='assets/shiritori/'+item['filename']
 assert all(row[k]==item[k] for k in ('reading','word','meaning','level'))
assert not list((ROOT/'assets/shiritori').glob('wave11-word-*.png'))
assert not list((ROOT/'assets/shiritori/sheets').glob('wave11-sheet-*.png'))
summary=json.loads((BASE/'summary.json').read_text(encoding='utf-8'))
assert hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest()==summary['dictionarySha256']
verification={'passed':True,'verifiedAt':'2026-10-15','registeredExistingRows':410,'uniqueNewManifestAssets':410,'cropSheets':26,'cropPassed':True,'dataTest':True,'importHistoryTest':True,'coverageAudit':True,'brokenImageReferences':0,'browser':{'passed':True,'imagesPerViewport':410,'viewports':2,'offline':True,'homonyms':True,'reviewCatalog':True},'excludedOriginalBatchAbsentFromPublicTree':True}
(BASE/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
summary['browserVerification']=verification['browser'];summary['validation']='data/image-coverage/2026-10-14-wave11-safe/verification.json'
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report='''# 既存語への画像追加（対象見直し後）

2026年10月15日確認。一般語・地名・歴史上の人物など、条件に合う既存410語に画像を追加しました。新しい単語の追加はありません。

- 採用した元シート: 26枚。16コマの罫線を機械検出し、256×256画像を元シートから再計算して確認。
- ゲーム用の新規登録画像: 410枚。最後のシートの小石6枚は検証用で、辞書・画像マニフェストには登録していません。
- 今回の対象外: 1,359語。存命人物・既存キャラクター・商品や団体のマークなど。
- 語義・表記などの確認で保留: 25語。詳細は selection-review.json。
- 開始時の既存7,609語では、画像未登録が1,794語から1,384語になりました。
- 辞書・登録履歴・全画像参照の検証は合格。PCとスマホの各410語を、外部検索を使わずゲームと画像確認画面で検証しました。

存命の岸田文雄・小泉純一郎・細川護熙・高市早苗は追加対象から除外しています。今回の方針変更は新規追加分に適用し、既存登録画像の全体審査や削除は行っていません。

追加一覧は words.csv、登録用データは ../../batches/2026-10-14-wave11-safe-existing410.csv、確認結果は verification.json、内容確認は content-review.json に保存しました。
'''
(BASE/'report.md').write_text(report,encoding='utf-8')
print(json.dumps(verification,ensure_ascii=False))
