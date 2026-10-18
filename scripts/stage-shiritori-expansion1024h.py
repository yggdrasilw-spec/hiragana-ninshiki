"""Stage one immutable generated sheet and verify measured grid crops."""
import argparse,importlib.util,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-18-expansion1024h'
p=argparse.ArgumentParser();p.add_argument('--sheet',type=int,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--version',default='');p.add_argument('--prompt-file',type=Path);a=p.parse_args()
s=json.loads((OUT/'sheets.json').read_text(encoding='utf-8'))[a.sheet-1];suffix='-'+a.version if a.version else ''
source=ROOT/'assets/shiritori/sheets'/f'expansion1024h-sheet{a.sheet:02}{suffix}.png';source.parent.mkdir(exist_ok=True)
assert not source.exists() or source.read_bytes()==a.source.read_bytes(),'Refuse overwrite'
if not source.exists():shutil.copyfile(a.source,source)
actual_prompt=s['prompt']
if a.sheet>=6 or a.version=='v3':
 actual_prompt+='\nStrict palette: NO pink, violet, purple or magenta in any object, fabric, flower, background or shadow. Use muted red/orange, blue/cyan, green, brown and neutral colors. Magenta is reserved exclusively for straight grid lines. All 4 rows and 4 columns MUST have identical dimensions, use the provided equal grid exactly, do not squeeze any row.'
if a.prompt_file:actual_prompt=a.prompt_file.read_text(encoding='utf-8')
prompt=source.with_suffix('.prompt.txt');prompt.write_text(actual_prompt,encoding='utf-8')
report=OUT/f'sheet{a.sheet:02}{suffix}-crop.json';output=ROOT/'assets/shiritori'
cmd=[sys.executable,'-B',str(ROOT/'scripts/crop-shiritori-grid.py'),str(source),'--names',','.join(Path(x['filename']).stem for x in s['tiles']),'--output',str(output),'--report',str(report)]
if report.exists():cmd.append('--verify-existing')
r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
record=dict(sheet=a.sheet,sourceSheet=source.relative_to(ROOT/'assets/shiritori').as_posix(),prompt=actual_prompt,cropValidation=report.relative_to(ROOT).as_posix(),passed=r.returncode==0,slots=[x['slot'] for x in s['tiles']])
(OUT/f'sheet{a.sheet:02}{suffix}-staged.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(r.stdout+r.stderr);sys.exit(r.returncode)
