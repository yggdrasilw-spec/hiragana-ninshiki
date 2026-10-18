"""Stage one generated sheet without replacing old evidence."""
import argparse,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-request25'
p=argparse.ArgumentParser();p.add_argument('sheet',type=int);p.add_argument('source',type=Path);p.add_argument('--version',default='');a=p.parse_args()
s=json.loads((OUT/'sheets.json').read_text(encoding='utf-8'))[a.sheet-1]
suffix='-'+a.version if a.version else ''
dest=ROOT/'assets/shiritori/sheets'/f'request25-sheet{a.sheet:02}{suffix}.png'
assert not dest.exists() or dest.read_bytes()==a.source.read_bytes()
if not dest.exists():shutil.copyfile(a.source,dest)
dest.with_suffix('.prompt.txt').write_text(s['prompt'],encoding='utf-8')
report=OUT/f'sheet{a.sheet:02}{suffix}-crop.json'
if a.version:
 for x in s['tiles']:x['filename']=x['filename'].replace('request25-','request25'+a.version+'-')
cmd=[sys.executable,'-B',str(ROOT/'scripts/crop-shiritori-grid.py'),str(dest),'--names',','.join(Path(x['filename']).stem for x in s['tiles']),'--output',str(ROOT/'assets/shiritori'),'--report',str(report)]
if report.exists():cmd.append('--verify-existing')
subprocess.run(cmd,cwd=ROOT,check=True)
