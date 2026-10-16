"""Keep source sheets, prompts and measured provisional crops before final IDs exist."""
import argparse, json, subprocess, sys, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/image-coverage/2026-10-16-expansion1024g'
REUSE={5:7434,81:140,165:7694,396:1038,693:928,774:257}
def save(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--sheet',type=int);parser.add_argument('--source',type=Path);parser.add_argument('--prompt-file',type=Path);parser.add_argument('--version',default='');args=parser.parse_args()
draft=json.loads((OUT/'draft.json').read_text(encoding='utf-8'))
items=[dict(x,slot=i+1) for i,x in enumerate(draft['items'])]
fresh=[x for x in items if x['slot'] not in REUSE]
assert len(items)==1024 and len(fresh)==1018
header='Use case: illustration-story. Asset type: Japanese elementary vocabulary illustrations. Edit the provided 2048x2048 template painting ONLY inside its sixteen white panels. Keep precisely the 4x4 equal grid and five continuous pure magenta #ff00ff lines in each direction including outer frame. Preserve line positions and thickness. Each panel is an independent clear gentle picture-book illustration on a light background, large and easily understood. Never use magenta for illustration. Nothing crosses the grid. No text, letters, numbers, labels or watermarks. For abstract words show a concrete situation illustrating the meaning. Diverse natural children and adults. Correct anatomy and objects. Panels in strict row-major order (left to right then top to bottom):\n'
sheets=[]
for n in range(64):
    tiles=fresh[n*16:n*16+16].copy()
    while len(tiles)<16: tiles.append(dict(tiles[-1],slot=2000+len(tiles),filler=True))
    prompt=header+'\n'.join(f"{i+1}. {x['word']} — {x['meaning']}" for i,x in enumerate(tiles))
    for i,x in enumerate(tiles):x.update(sheet=n+1,tileIndex=i+1)
    sheets.append(dict(sheet=n+1,tiles=tiles,prompt=prompt,sourceSheet=f'sheets/expansion1024g-sheet{n+1:02}.png'))
save(OUT/'sheets.json',sheets)
if args.sheet:
    sheet=sheets[args.sheet-1]
    suffix=('-'+args.version) if args.version else ''
    if suffix:sheet['sourceSheet']=f'sheets/expansion1024g-sheet{args.sheet:02}{suffix}.png'
    dest=ROOT/'assets/shiritori'/sheet['sourceSheet']
    assert args.source and args.source.is_file()
    assert not dest.exists() or dest.read_bytes()==args.source.read_bytes(), 'Never overwrite an existing source sheet'
    if not dest.exists(): shutil.copyfile(args.source,dest)
    prompt=args.prompt_file.read_text(encoding='utf-8') if args.prompt_file else sheet['prompt']
    prompt_path=dest.with_suffix('.prompt.txt')
    if not prompt_path.exists():prompt_path.write_text(prompt,encoding='utf-8')
    output=OUT/'crop-staging'/f'sheet{args.sheet:02}{suffix}'
    report=OUT/f'sheet{args.sheet:02}{suffix}-staging-crop.json'
    cmd=[sys.executable,'-B',str(ROOT/'scripts/crop-shiritori-grid.py'),str(dest),'--names',','.join(f"expansion1024g-slot-{x['slot']}" for x in sheet['tiles']),'--output',str(output),'--report',str(report)]
    if report.exists():cmd.append('--verify-existing')
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    save(OUT/f'sheet{args.sheet:02}{suffix}-staged.json',dict(sheet=sheet['sheet'],sourceSheet=sheet['sourceSheet'],prompt=prompt,tiles=sheet['tiles'],report=str(report.relative_to(ROOT)),outputDirectory=str(output.relative_to(ROOT)),passed=result.returncode==0))
    print(json.dumps(dict(sheet=args.sheet,passed=result.returncode==0,output=result.stdout+result.stderr),ensure_ascii=False))
    sys.exit(result.returncode)
print('Prepared 64 sheets / 1018 new pictures / 6 existing shared pictures')
