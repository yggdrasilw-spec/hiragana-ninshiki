"""Save generated sheet evidence and crop only from measured magenta lines."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c'
p=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
ap=argparse.ArgumentParser();ap.add_argument('sheet',type=int);ap.add_argument('source',type=Path);a=ap.parse_args()
items=[x for x in p['newImages'] if x['sheet']==a.sheet]
dest=ROOT/'assets/shiritori'/items[0]['sourceSheet']
if dest.exists():assert dest.read_bytes()==a.source.read_bytes(),'Never overwrite sheet evidence'
else:shutil.copyfile(a.source,dest)
dest.with_suffix('.prompt.txt').write_text(items[0]['prompt'],encoding='utf-8')
names=[x['filename'][:-4] for x in items]+[f'expansion512c-filler-sheet{a.sheet:02}-{i}' for i in range(len(items)+1,17)]
cmd=[sys.executable,'-X','utf8','scripts/crop-shiritori-grid.py',str(dest),'--names',','.join(names),'--output',str(ROOT/'assets/shiritori'),'--report',str(ROOT/items[0]['cropValidation'])]
if (ROOT/items[0]['cropValidation']).exists():cmd.append('--verify-existing')
subprocess.run(cmd,cwd=ROOT,check=True)
