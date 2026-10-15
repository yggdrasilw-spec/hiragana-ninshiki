"""Measure grid lines; preserve every tile and fail closed on unstable sheets."""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-15-expansion512e'
ap=argparse.ArgumentParser();ap.add_argument('--sheets',default=','.join(map(str,range(1,11))));args=ap.parse_args()
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));by_slot={x['slot']:x for x in plan['items']}
music=json.loads((OUT/'music-plan.json').read_text(encoding='utf-8'))
for x in music['items']:
 if x['filler']:x['filename']=f'expansion512e-music-filler-{x["tileIndex"]:02}.png'
 else:
  word=by_slot[x['slot']];assert word.get('id') and word['reading']==x['reading']
  x.update(id=word['id'],filename=f'expansion512e-music-word-{word["id"]}.png')
for sheet in map(int,args.sheets.split(',')):
 group=[x for x in music['items'] if x['sheet']==sheet]
 report=OUT/f'music-sheet{sheet:02}-crop.json'
 cmd=[sys.executable,'-X','utf8','scripts/crop-shiritori-grid.py',str(ROOT/'assets/shiritori'/group[0]['sourceSheet']),'--names',','.join(x['filename'][:-4] for x in group),'--output','assets/shiritori','--report',str(report)]
 if report.exists():cmd.append('--verify-existing')
 subprocess.run(cmd,cwd=ROOT,check=True)
 for x in group:x['cropValidation']=str(report.relative_to(ROOT)).replace('\\','/')
(OUT/'music-plan.json').write_text(json.dumps(music,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(sheets=args.sheets,gridVerified=True)))
