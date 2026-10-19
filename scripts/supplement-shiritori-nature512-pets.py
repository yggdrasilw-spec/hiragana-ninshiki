import json,csv,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512';p=json.loads((O/'plan.json').read_text(encoding='utf-8'))
assert len(p['items'])==512,'Supplement may only be appended once'
existing=list(csv.DictReader((R/'whitelist.csv').read_text(encoding='utf-8').splitlines()));readings={r['reading'] for r in existing+p['items']}
for line in (O/'pet-supplement.txt').read_text(encoding='utf-8').splitlines():
 reading,word,meaning,sci,scene=line.split('|');assert reading not in readings,reading;readings.add(reading);g,sp=sci.split()
 slot=len(p['items'])+1;x=dict(reading=reading,word=word,meaning=meaning+' 学名：'+sci+'。',scientificName=sci,scene=scene,category='reptiles',grade=4,level=3,lexicalSource=dict(url=f'https://reptile-database.reptarium.cz/{g}/{sp}',lookupWord=word,scientificName=sci),meaningReason='ペットとして知られる主要な爬虫類の取りこぼしを補う。種名と学名を対応。',ageReason='専門的な種の名前としてレベル4。',imageReason='当該種の体型・模様・脚・尾を照合した教育用イラスト。'+scene,slot=slot,sheet=(slot-1)//16+1,tileIndex=(slot-1)%16+1,filename=f'nature512-slot-{slot:03}.png');p['items'].append(x)
assert len(p['items'])==544
prefix=p['sheets'][0]['prompt'].split('Exact order:\n')[0]+'Exact order:\n'
for n in [33,34]:
 tiles=[x for x in p['items'] if x['sheet']==n];prompt=prefix+'\n'.join(f'{i+1}. {x["word"]}: {x["scene"]}.' for i,x in enumerate(tiles));p['sheets'].append(dict(sheet=n,tiles=tiles,prompt=prompt));(O/f'sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8')
p['target']=512;p['supplement']=32;p['scopeReason']='ペットとして知られる主要32種の未掲載を補い544語とする。'
(O/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Supplemented 32 familiar pet reptile species; total 544.')
