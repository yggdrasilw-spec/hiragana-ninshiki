"""Reserve the three element homonyms without overwriting unrelated senses."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
p=json.loads((O/'plan.json').read_text(encoding='utf-8'));els=json.loads((O/'elements.json').read_text(encoding='utf-8'))
replacements=[]
for slot,reading in [(508,'りん'),(509,'すず'),(510,'らんたん')]:
 old=p['items'][slot-1];e=next(e for e in els if e['reading']==reading)
 x=dict(e,category='elements',grade=4,level=3,scientificName='',lexicalSource=dict(url='https://iupac.org/what-we-do/periodic-table-of-elements/',atomicNumber=e['atomicNumber'],symbol=e['symbol']),meaningReason='元素の原子番号・記号・日本語名を対応。',ageReason='専門的な化学の意味としてレベル4。',imageReason='元素または用途の説明イメージ。',distinctSenseReason='同じ読みの既存語はキャラクター・鈴・照明器具の意味。今回は化学元素としての別の意味。',slot=slot,sheet=32,tileIndex=slot-496,filename=f'nature512-slot-{slot:03}.png')
 p['items'][slot-1]=x;replacements.append(dict(slot=slot,before=old,after=x))
s=p['sheets'][31];s['tiles']=[x for x in p['items'] if x['sheet']==32]
prefix=s['prompt'].split('Exact order:\n')[0]+'Exact order:\n';s['prompt']=prefix+'\n'.join(f'{i+1}. {x["word"]}: {x["scene"]}.' for i,x in enumerate(s['tiles']))
(O/'sheet32.prompt.txt').write_text(s['prompt'],encoding='utf-8')
(O/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'element-homonyms.json').write_text(json.dumps(replacements,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Replaced three duplicate mineral names with the three missing element senses.')
