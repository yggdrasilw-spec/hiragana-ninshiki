import sys,json,shutil,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
n=int(sys.argv[1]);source=Path(sys.argv[2]);target=R/f'assets/shiritori/sheets/nature512-sheet{n:02}.png'
assert source.is_file() and source.suffix=='.png'
version=1
while target.exists() and target.read_bytes()!=source.read_bytes():
 version+=1;target=R/f'assets/shiritori/sheets/nature512-sheet{n:02}-v{version}.png'
if not target.exists():shutil.copy2(source,target)
p=json.loads((O/'plan.json').read_text(encoding='utf-8'));s=p['sheets'][n-1]
shutil.copy2(O/f'sheet{n:02}.prompt.txt',target.with_suffix('.prompt.txt'))
names=','.join(Path(x['filename']).stem for x in s['tiles'])
suffix='' if version==1 else f'-v{version}'
report=O/f'sheet{n:02}{suffix}-crop.json';out=O/f'crop-staging/sheet{n:02}{suffix}'
cmd=[sys.executable,'-X','utf8',str(R/'scripts/crop-shiritori-grid.py'),str(target),'--method','magenta-grid-lines-only-v4','--names',names,'--output',str(out),'--report',str(report)]
if report.exists():cmd+=['--verify-existing']
subprocess.run(cmd,cwd=R,check=True)
record=dict(sheet=n,source=target.relative_to(R).as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),mechanicalPassed=True,cropValidation=report.relative_to(R).as_posix(),staging=out.relative_to(R).as_posix())
(O/f'sheet{n:02}-staged.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record))
