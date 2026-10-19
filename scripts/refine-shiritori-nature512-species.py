import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512';p=json.loads((O/'plan.json').read_text(encoding='utf-8'))
fixes={
'こくしーべにへび':dict(reading='こくしーべになめら',word='コクシーベニナメラ',scientificName='Oreocryptophis porphyraceus coxi',meaning='タイなどに分布するベニナメラの亜種。赤い体に二本の黒い縦線がある。 学名：Oreocryptophis porphyraceus coxi。'),
'あかくちみずへび':dict(reading='えんひどりすえんひどりす',word='エンヒドリス・エンヒドリス',meaning='東南アジアの水辺などにすむヘビ。細長い体に縦の線がある。学名をカタカナで表した呼び名。 学名：Enhydris enhydris。'),
'おおひるやもり':dict(reading='ぐらんでぃすひるやもり',word='グランディスヒルヤモリ'),
'もりどらごん':dict(reading='ひぷしるるすでぃろふす',word='ヒプシルルス・ディロフス',meaning='ニューギニア周辺などにすむ樹上性トカゲの一種。首や背中にとさか状のうろこが並ぶ。学名をカタカナで表した呼び名。 学名：Hypsilurus dilophus。'),
'ふちあめかいまん':dict(reading='ぱれおすくすとりごなとぅす',word='パレオスクス・トリゴナトゥス',meaning='南アメリカにすむ小型のカイマンの一種。学名をカタカナで表した呼び名。 学名：Paleosuchus trigonatus。'),
'にたちざめ':dict(reading='よごれ',word='ヨゴレ',meaning='暖かい海の外洋にすむサメ。長い胸びれと背びれの先が丸く白い。 学名：Carcharhinus longimanus。',distinctSenseReason='既存の「汚れ」は表面についたほこりやしみの意味。こちらはサメの一種の名前。')}
changes=[]
for x in p['items']:
 if x['reading'] in fixes:
  before=dict(x);x.update(fixes[x['reading']]);s=x['scientificName'];g,sp=s.split()[:2]
  x['lexicalSource'].update(lookupWord=x['word'],scientificName=s,url=f'https://reptile-database.reptarium.cz/{g}/{sp}' if x['category']=='reptiles' else f'https://animaldiversity.org/accounts/{g}_{sp}/')
  changes.append(dict(slot=x['slot'],before=before,after=dict(x)))
for s in p['sheets']:
 s['tiles']=[x for x in p['items'] if x['sheet']==s['sheet']]
 prefix=s['prompt'].split('Exact order:\n')[0]+'Exact order:\n';s['prompt']=prefix+'\n'.join(f'{i+1}. {x["word"]}: {x["scene"]}.' for i,x in enumerate(s['tiles']))
 (O/f'sheet{s["sheet"]:02}.prompt.txt').write_text(s['prompt'],encoding='utf-8')
assert len({x['reading'] for x in p['items']})==512
(O/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(O/'species-refinement.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Refined',len(changes),'names against taxonomic and Japanese-name evidence.')
