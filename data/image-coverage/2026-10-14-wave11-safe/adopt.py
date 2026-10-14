import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
BASE=Path(__file__).resolve().parent
state_path=BASE/'generated-state-final.json'
if not state_path.exists():state_path=BASE/'generated-state.json'
state=json.loads(state_path.read_text(encoding='utf-8'))
plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'))
records=json.loads((BASE/'generation-records.json').read_text(encoding='utf-8'))
by_sheet={r['sheet']:r for r in records}
fixes={r['sheet']:r for r in state['revisions']}
for r in state['generated']:by_sheet[r['sheet']]=r
for s in state['pendingRevisions']:
 if s not in fixes:by_sheet.pop(s,None)
for s,fix in fixes.items():
 for item in [r for r in plan if r['sheet']==s]:
  version=fix.get('revision',1)
  item['revision']=version
  item['filename']=f'wave11-safe-r{version}-word-{item["id"]}.png'
  item['sourceSheet']=f'sheets/wave11-safe-sheet-{s:02}-r{version}.png'
  item['cropValidation']=f'data/image-coverage/2026-10-14-wave11-safe/crop-{s:02}-r{version}.json'
  if fix.get('regeneratedFromBlank'):item['prompt']=fix['prompt']
  else:item['prompt']=item['prompt'].split('\n\nSUBSEQUENT EDIT:\n')[0]+'\n\nSUBSEQUENT EDIT:\n'+fix['prompt']
 by_sheet[s]=fix
for s,rec in by_sheet.items():
 date=datetime.fromtimestamp(Path(rec['path']).stat().st_mtime,timezone.utc).astimezone(timezone(timedelta(hours=9))).date().isoformat()
 for item in [r for r in plan if r['sheet']==s]:
  item['generatedAt']=date
  (BASE/f'prompt-{s:02}.txt').write_text(item['prompt'],encoding='utf-8')
(BASE/'generation-records.json').write_text(json.dumps([by_sheet[s] for s in sorted(by_sheet)],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(BASE/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Ready sheets',len(by_sheet),'pending',[s for s in range(1,27) if s not in by_sheet])
