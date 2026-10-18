"""Rebase frozen vocabulary IDs after another authorized dictionary batch lands."""
import argparse,csv,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-culture512'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));base=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(base.decode('utf-8').splitlines()))
assert len(rows)>plan['baselineRows']
existing={r['reading'] for r in rows};before_count=plan['baselineRows'];delta=len(rows)-before_count
changes={
 'ぐんぐにる':('おーでぃんのやり','オーディンの槍','北欧神話に登場するグングニルを指す呼び名。神オーディンが持つとされる槍。','https://www.gutenberg.org/ebooks/18947'),
 'みょるにる':('とーるのつち','トールの槌','北欧神話に登場するミョルニルを指す呼び名。雷の神トールが持つとされるつち。','https://natmus.dk/nyhed/runer-bekraefter-thors-hammer-er-en-hammer/'),
 'あめのぬぼこ':('あまのぬほこ','天の瓊矛','日本神話で国生みに使われたとされる、玉で飾った矛。天沼矛とも表記される。','https://kotobank.jp/word/天の瓊矛-427139')}
record=[]
for x in plan['items']:
 oldid=x['id'];oldreading=x['reading']
 if oldreading in existing:
  assert oldreading in changes,oldreading
  reading,word,meaning,url=changes[oldreading];assert reading not in existing
  record.append(dict(beforeReading=oldreading,afterReading=reading,word=word,reason='別バッチに先に登録された同じ武器名を重ねず、同一対象の別呼称として登録。',source=url))
  x.update(reading=reading,word=word,meaning=meaning)
  x['lexicalSource']=dict(primaryReference=dict(name='神話原典・辞典・博物館の呼称資料',url=url),sameObjectReading=oldreading,referenceDate='2026-10-19')
  x['meaningReason']='すでに登録された'+oldreading+'と同じ神具・武器を指す別呼称。別の実物や別の神具を作らない。'
  x['scene']=x['scene'].replace({'ぐんぐにる':'グングニル','みょるにる':'ミョルニル','あめのぬぼこ':'天沼矛'}[oldreading],word)
  x['imageReason']='同一の伝説上の武器を表す説明イラスト。実物の復元写真ではない。'+x['scene']
 x['id']+=delta
 x['filename']=f'culture512-word-{x["id"]}.png'
 if x.get('sharedWithId'):x['sharedWithId']+=delta
for x in plan['items']:
 if x.get('aliasOf'):x['filename']=next(y['filename'] for y in plan['items'] if y['reading']==x['aliasOf'])
assert len({x['reading'] for x in plan['items']})==512
assert not {x['reading'] for x in plan['items']}&existing
baseline=OUT/'registration-baseline.csv';oldbaseline=OUT/f'baseline-before-rebase-{before_count}.csv';assert not oldbaseline.exists();baseline.rename(oldbaseline);baseline.write_bytes(base)
plan.update(baselineRows=len(rows),baselineSha256=hashlib.sha256(base).hexdigest())
sheets=json.loads((OUT/'sheets.json').read_text(encoding='utf-8'))
for s in sheets:s['tiles']=[x for x in plan['items'] if x['sheet']==s['sheet'] and not x.get('aliasOf')]
save(OUT/'plan.json',plan);save(OUT/'sheets.json',sheets);save(OUT/'rebase-review.json',dict(previousRows=before_count,currentRows=len(rows),delta=delta,changes=record))
versions=json.loads((OUT/'sheet-versions.json').read_text(encoding='utf-8'))
for n in range(1,31):
 suffix='-'+versions[str(n)] if str(n) in versions else ''
 source=ROOT/'assets/shiritori/sheets'/f'culture512-sheet{n:02}{suffix}.png'
 report=OUT/f'sheet{n:02}{suffix}-crop.json'
 archived=report.with_name(report.stem+f'-before-rebase-{before_count}.json');assert not archived.exists();report.rename(archived)
 cmd=[sys.executable,'-B','-X','utf8','scripts/stage-shiritori-culture512.py',str(n),str(source)]
 if suffix:cmd+=['--version',versions[str(n)]]
 subprocess.run(cmd,cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
print(json.dumps(dict(rebased=True,baselineRows=len(rows),recroppedSheets=30,changes=record),ensure_ascii=False))
