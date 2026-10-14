import csv,json,re,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
PRIVATE=Path('C:/Users/user/.codex/artifacts/shiritori-wave11-20261014/review')
old=json.loads((PRIVATE/'plan.json').read_text(encoding='utf-8'))
rows=json.loads((PRIVATE/'before-rows.json').read_text(encoding='utf-8'))
living={'岸田文雄','小泉純一郎','細川護熙','高市早苗'}
character_ids={901,2029,2835,3415,4131,4174,4289,4770,4774,5353,5870}
brand_ids={290,1624,2107,3541,3658,5095,5796,5892}
editorial_ids={297,456,520,552,617,705,714,812,1203,1257,1604,1755,1767,1819,2646,2666,3020,3082,3131,3132,3133,3137,3459,3915,6036}
pattern='ポケモン|プリキュア|ガンダム|メガシンカ|アローラ|ガラル|ヒスイ|キタカミ|進化|姿|シェルダー|ウルトラビースト|登場|キャラクター|アニメ|モビル|ジオン|ディズニー|Nintendo|Pok[eé]mon'
eligible=[];excluded=[];pending=[]
for i,r in enumerate(rows,1):
 if r['image_asset']:continue
 item=dict(id=i,**r)
 if r['word'] in living:reason='存命の人物。ユーザー指定により今回の画像追加から除外。'
 elif i in brand_ids:reason='商品・企業・団体・現代作品の名称。ユーザー指定を受け、ロゴや既存デザインを避けて今回は保留。'
 elif i in character_ids or re.search(pattern,r['meaning']+r['word']+r['imagequery']):reason='既存キャラクター・作品等の画像候補。今回の対象から除外。'
 elif i in editorial_ids:
  pending.append(dict(**item,reason='語義や表記、識別対象に確認事項があり、正確な画像を確定するまで保留。'));continue
 else:eligible.append(item);continue
 excluded.append(dict(**item,reason=reason))
ids={r['id'] for r in eligible}
reuse=[]
for n in range(1,25):
 group=[r for r in old if r['sheet']==n]
 if len(group)==16 and all(r['id'] in ids for r in group):reuse.append(group)
assigned={r['id'] for group in reuse for r in group}
remaining=sorted([r for r in eligible if r['id'] not in assigned],key=lambda r:r['id'])
groups=[(group,True) for group in reuse]+[(remaining[j:j+16],False) for j in range(0,len(remaining),16)]
plan=[];records=[]
prefix='Edit the attached blank equal-size 4x4 template. Paint EXACTLY 16 independent watercolor picture-book illustrations in row-major order. Preserve ALL FIVE horizontal and FIVE vertical straight continuous pure MAGENTA #ff00ff grid lines INCLUDING OUTER FRAME, exact equal cell geometry. Magenta is ONLY for grid: artwork uses blue, green, orange, gold, brown and neutral colors; avoid fuchsia and violet pigments. Complete scenes stay in their cells, use each cell generously, no required white margins. No labels, captions, numbers or letters except intentional notation specifically requested in a cell. NO copyrighted characters, logos, recognizable modern branded products or living public figures. Historical people must match their era and distinctive appearance, not another historical person. Generic roles such as prime minister or emperor should use buildings or a fictional unidentifiable figure, not a recognizable recent politician. Places use characteristic geography or older historical buildings, no invented maps or flags. Chemistry must show correct equipment, no inaccurate molecular model. Subjects in exact order:\n'
for s,(group,reused) in enumerate(groups,1):
 for t,r in enumerate(group,1):
  item=dict(r);item.update(sheet=s,tileIndex=t,filename=f'wave11-safe-word-{r["id"]}.png',sourceSheet=f'sheets/wave11-safe-sheet-{s:02}.png',generatedAt='2026-10-14',cropValidation=f'data/image-coverage/2026-10-14-wave11-safe/crop-{s:02}.json')
  if not reused:item['scene']=f'{r["word"]} ({r["reading"]}; {r["imagequery_en"]}): {r["meaning"]}'
  plan.append(item)
 if reused:
  old_sheet=Path('C:/Users/user/.codex/artifacts/shiritori-wave11-20261014/sheets')/Path(group[0]['sourceSheet']).name
  records.append(dict(sheet=s,path=str(old_sheet),reusedOriginalSheet=group[0]['sheet']))
  prompt=group[0]['prompt']
 else:
  prompt=prefix+'\n'.join(f'{t}. {r["scene"]}' for t,r in enumerate([r for r in plan if r['sheet']==s],1))
  for t in range(len(group)+1,17):prompt+=f'\n{t}. Filler cell: a simple smooth grey pebble. This cell is not a dictionary assignment.'
 for r in plan:
  if r['sheet']==s:r['prompt']=prompt
 (BASE/f'prompt-{s:02}.txt').write_text(prompt,encoding='utf-8')
(BASE/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'generation-records.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'before-rows.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'selection-review.json').write_text(json.dumps(dict(eligibleRows=len(eligible),excludedRows=len(excluded),editorialPendingRows=len(pending),excluded=excluded,pending=pending,criteria='ユーザー指定: 歴史上の人物は対象に残す。存命人物・既存キャラクター・商品団体のマークを除外。一般語と地名はオリジナル画像。'),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(eligibleRows=len(eligible),excludedRows=len(excluded),editorialPendingRows=len(pending),sourceSheets=len(groups),reusedSheets=len(reuse),generateSheets=list(range(len(reuse)+1,len(groups)+1))),ensure_ascii=False))
