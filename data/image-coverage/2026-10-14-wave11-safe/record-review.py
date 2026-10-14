import json,csv
from pathlib import Path
BASE=Path(__file__).resolve().parent
plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'))
notes=json.loads((BASE/'review-notes.json').read_text(encoding='utf-8'))
notes['corrections']['12']='罫線の縁と、桜などの罫線色に近い色を修正。コマの語順と描画範囲を維持。'
notes['corrections']['15']='県は窓口業務の場面。肛門は外部の体ではなく消化管の末端を示す模式図。空気調節は燃料弁ではなく空気穴のある筒の回転。花の罫線色混入も修正。'
notes.pop('acceptedSheetsBeforeFinalGridRepairs',None)
notes['acceptedSheets']=list(range(1,27))
notes['wordReviews']=[{k:r[k] for k in ('id','reading','word','meaning','filename','sourceSheet','tileIndex')}|{'status':'reviewed','review':'採用シートでコマ順と被写体・場面を語義と照合。切り出しの合否は別の機械検証記録で確認。'} for r in plan]
notes['sourcesConsulted'][1]['use']='近代の歴史人物の情報の参照。公開写真そのものを転載するバッチではない。'
(BASE/'content-review.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
with (BASE/'words.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=['id','reading','word','meaning','filename'],extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(plan)
print('Recorded visual subject review for',len(plan),'words in 26 sheets')
