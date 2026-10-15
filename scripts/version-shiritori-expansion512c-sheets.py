"""Version failed sheets before regeneration, retaining rejected evidence."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent;OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c';P=OUT/'plan.json'
p=json.loads(P.read_text(encoding='utf-8'));numbers={int(n) for n in sys.argv[1].split(',')};version=sys.argv[2] if len(sys.argv)>2 else 'v2'
for x in p['newImages']:
 if x['sheet'] not in numbers:continue
 n=x['sheet'];x.update(sourceSheet=f'sheets/expansion512c-sheet{n:02}-{version}.png',cropValidation=f'data/image-coverage/2026-10-15-expansion512c/sheet{n:02}-{version}-crop.json')
 if 'STRICT COLOR' not in x['prompt']:x['prompt']+='\nSTRICT COLOR: NO pink, purple, violet, fuchsia, rose, lavender or magenta in the artwork. Every bag, decoration, object, background, food plate, clothing and display must use blue, green, cyan, orange, tan, brown or neutral colors. Only grid lines are magenta. Preserve ALL TEN continuous straight grid lines, four EQUAL rows and four EQUAL columns, exact visible OUTER FRAME. No faded or broken line. Do not add extra grid lines. Crisp magenta must not bleed into cells.'
P.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps([dict(sheet=n,prompt=next(x['prompt'] for x in p['newImages'] if x['sheet']==n)) for n in sorted(numbers)],ensure_ascii=False))
