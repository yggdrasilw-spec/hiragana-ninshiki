"""Repeat related-form/compound intake to a fixed point with durable batches.

Without --apply only the next concrete batch is prepared. Fetch upstream and
use a current isolated worktree. Existing decisions and held items are retained.
"""
import argparse,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion'
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
 out=R/'qa-output/lexical-expansion';out.mkdir(parents=True,exist_ok=True)
 records=[];number=2
 while True:
  batch=f'2026-11-16-related-closure-{number:02d}';sf=R/'data/dictionary-imports'/f'{batch}.summary.json'
  if sf.exists() and json.loads(sf.read_text(encoding='utf-8')).get('registered'):
   number+=1;continue
  for script in ['scan-shiritori-source-aliases.py','prepare-shiritori-compound-closure.py']:
   with (out/f'{batch}-{script}.log').open('w',encoding='utf-8') as f:
    subprocess.run([sys.executable,'-B','-X','utf8','scripts/'+script],cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
  command=[sys.executable,'-B','-X','utf8','scripts/import-shiritori-related-closure.py','--batch',batch]
  if args.apply:command.append('--apply')
  completed=subprocess.run(command,cwd=R,text=True,encoding='utf-8',capture_output=True)
  (out/f'{batch}-import.log').write_text(completed.stdout+completed.stderr,encoding='utf-8')
  if completed.returncode:print(completed.stdout+completed.stderr);raise RuntimeError('Import failed; its checkpoint supports recovery: '+batch)
  summary=json.loads(completed.stdout.strip().splitlines()[-1]);records.append(summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
  if not args.apply or not summary.get('added'):break
  number+=1
 if args.apply:
  for script in ['audit-shiritori-lexical-families.py','walk-shiritori-related-words.py']:
   subprocess.run([sys.executable,'-B','-X','utf8','scripts/'+script],cwd=R,check=True)
 checkpoint=dict(schema=1,applied=args.apply,rounds=records,stoppedBecause='no-more-admissible-current-source-rules' if args.apply else 'prepared-for-review',
  remaining='Source and meaning holds remain in the queues; a source-reference fixed point is not full lexical coverage.')
 (D/'expansion-checkpoint.json').write_text(json.dumps(checkpoint,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
