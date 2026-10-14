import json,subprocess,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
plan=json.loads((BASE/'plan.json').read_text(encoding='utf-8'))
records=json.loads((BASE/'generation-records.json').read_text(encoding='utf-8'))
failed=[]
for rec in records:
 s=rec['sheet'];group=[r for r in plan if r['sheet']==s]
 source=ROOT/'assets/shiritori'/group[0]['sourceSheet']
 if not source.exists():shutil.copyfile(rec['path'],source)
 report=ROOT/group[0]['cropValidation'];suffix=group[0].get('revision',0)
 out=BASE/(f'tiles-{s:02}-r{suffix}' if suffix else f'tiles-{s:02}')
 # Last sheet has ten dictionary subjects and six unassigned filler cells.
 names=[r['filename'][:-4] for r in group]+[f'wave11-safe-filler-{s:02}-{t:02}' for t in range(len(group)+1,17)]
 command=[sys.executable,'-B',str(ROOT/'scripts/crop-shiritori-grid.py'),str(source),'--names',','.join(names),'--output',str(out),'--report',str(report)]
 if report.exists():command+=['--verify-existing']
 result=subprocess.run(command,cwd=ROOT)
 if result.returncode:failed.append(s)
 print('SHEET',s,'PASSED' if result.returncode==0 else 'REJECTED',flush=True)
(BASE/'crop-status.json').write_text(json.dumps(dict(sheets=len(records),rejected=failed),indent=2)+'\n',encoding='utf-8')
sys.exit(bool(failed))
