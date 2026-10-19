"""Apply documented taxon/name review before generating animal sheets."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
p=json.loads((O/'plan.json').read_text(encoding='utf-8'));changes=[]
fixes={
 'ひめあいぞめやどくがえる':('らにとめやいみてーたー','ラニトメヤ・イミテーター',None,None,None),
 'ぞうげいろやどくがえる':('ふたいろふきやがえる','フタイロフキヤガエル',None,None,None),
 'さんさんなめら':('こえろぐなとぅすふらぼりねあとぅす','コエログナトゥス・フラボリネアトゥス',None,None,None),
 'たかさごなめら':('たかさごなめら','タカサゴナメラ','Euprepiophis mandarina','東アジアから東南アジアの山地などにすむヘビ。灰色の体に黒と黄色の大きな模様がある。','Gray Mandarin rat snake with large black diamonds containing yellow centers and black-yellow head bars.'),
 'みどりなめら':('あかおなめら','アカオナメラ',None,'東南アジアにすむ緑色の樹上性のヘビ。尾が赤褐色になるものがある。',None),
 'たいりくしまへび':('さらさなめら','サラサナメラ',None,None,None),
 'ろしあなめら':('からだいしょう','カラダイショウ',None,None,None),
 'なげすなぼあ':('いんどすなぼあ','インドスナボア',None,None,None),
 'すなふぃっしゅ':('ないるすなとかげ','ナイルスナトカゲ',None,None,None),
 'なきやもり':('ほおぐろやもり','ホオグロヤモリ',None,'熱帯地域などに分布する小型のヤモリ。人家の周りにも見られる。','Pale gray house gecko with dark cheek stripe granular back broad toe pads and slender banded tail.'),
 'きがしらひるやもり':('ひろおひるやもり','ヒロオヒルヤモリ',None,'マダガスカルなどにすむ昼行性のヤモリ。頭の金色の細かな点や赤い背中の模様が目立つ。',None),
 'まつかさやもり':('まつかさやもり','マツカサヤモリ','Hemidactylus imbricatus','パキスタンなどにすむ小型のヤモリ。大きなうろこと松かさのような太い尾を持つ。','Small ground viper gecko with overlapping keeled scales gray-brown dorsal pattern and fat pinecone-like tapering tail.'),
 'ばいのとりつめやもり':('ばいのとりのつめやもり','バイノトリノツメヤモリ',None,None,None),
 'なめはだたまおやもり':('なめはだたまおやもり','ナメハダタマオヤモリ',None,None,None),
 'はなながくびがめ':('またまた','マタマタ',None,'南アメリカにすむ平たい頭と皮膚のひだが目立つカメ。',None),
 'あかはらへびくびがめ':('あかはらまげくびがめ','アカハラマゲクビガメ',None,None,None),
 'ぬまよこくびがめ':('ぬまよこくびがめ','ヌマヨコクビガメ',None,None,None),
 'きょくとうさそり':('もんごるさそり','モンゴルサソリ','Olivierus martensii','アジア東部にすむ毒を持つサソリ。キョクトウサソリと呼ばれることもある。',None),
 'つますずめばち':('つまあかすずめばち','ツマアカスズメバチ',None,None,None),
 'きたかぎのてくらげ':('かぎのてくらげ','カギノテクラゲ',None,'小さな傘と多数の触手を持つクラゲの仲間。刺されると強い症状を起こすことがある。',None),
 'くりいろどろがめ':('さそりどろがめ','サソリドロガメ',None,'中南米にすむドロガメの仲間。甲羅に三本の隆起が見られる。',None),
 'ひらおりくがめ':('ひらおくものすがめ','ヒラオクモノスガメ',None,None,None),
 'ほしやぶがめ':('くものすがめ','クモノスガメ',None,None,None),
 'べるせおれがめ':('べるせおれがめ','ベルセオレガメ',None,'アフリカにすむ甲羅の後ろを曲げられるリクガメの仲間。',None),
 'とりころーるやどくがえる':('えぴぺどばてすとりころーる','エピペドバテス・トリコロール',None,None,None),
 'あめりかくろくま':('あめりかくろくま','アメリカクロクマ',None,None,None)}
frog_trans={
 'ばりあびりすやどくがえる':('らにとめやばりあびりす','ラニトメヤ・バリアビリス'),
 'べんとりまくらーたやどくがえる':('らにとめやべんとりまくらーた','ラニトメヤ・ベントリマクラータ'),
 'あまぞにかやどくがえる':('らにとめやあまぞにか','ラニトメヤ・アマゾニカ'),
 'ふぁんたすてぃかやどくがえる':('らにとめやふぁんたすてぃか','ラニトメヤ・ファンタスティカ'),
 'さまーずやどくがえる':('らにとめやさまーし','ラニトメヤ・サマーシ'),
 'しれんしすやどくがえる':('らにとめやしれんしす','ラニトメヤ・シレンシス'),
 'うあかりーやどくがえる':('らにとめやうあかりー','ラニトメヤ・ウアカリー'),
 'べねでぃくたやどくがえる':('らにとめやべねでぃくた','ラニトメヤ・ベネディクタ'),
 'みすてりおさすやどくがえる':('えくしどばてすみすてりおすす','エクシドバテス・ミステリオスス'),
 'はらまだらやどくがえる':('あめーれがびりんぐいす','アメーレガ・ビリングイス')}
for k,v in frog_trans.items():fixes[k]=(*v,None,None,None)
for x in p['items']:
 before=dict(x)
 if x['reading'] in fixes:
  reading,word,sci,meaning,scene=fixes[x['reading']];x.update(reading=reading,word=word)
  if sci:x['scientificName']=sci
  if meaning:x['meaning']=meaning+' 学名：'+x['scientificName']+'。'
  elif sci:x['meaning']=re.sub('学名：[^。]+。','学名：'+sci+'。',x['meaning'])
  if scene:x['scene']=scene
  if x['word'].startswith(('ラニトメヤ','エクシドバテス','エピペドバテス','アメーレガ','コエログナトゥス')):x['meaning']+='学名をカタカナで表した呼び名。'
 if x['reading']=='すてぃむそんぱいそん':
  x['scientificName']='Antaresia childreni';x['meaning']='オーストラリア内陸部などのチルドレンパイソンの地域型につけられた呼び名。旧学名はAntaresia stimsoni。独立種としない分類もある。'
 if x['category']=='frogs':x['meaningReason']='AmphibiaWebのヤドクガエル科リストで学名と種を照合。和名が一定しない種は学名のカタカナ表記を採用。'
 if x['category'] in ['reptiles','danger','toxic','frogs']:
  sci=x['scientificName'];g,sp=sci.split()[:2]
  url=(f'https://reptile-database.reptarium.cz/{g}/{sp}' if x['category']=='reptiles' else 'https://amphibiaweb.org/lists/Dendrobatidae.shtml' if x['category']=='frogs' else 'https://animaldiversity.org/accounts/'+g+'_'+sp+'/')
  x['lexicalSource'].update(url=url,scientificName=sci,lookupWord=x['word'])
 if before!=x:changes.append(dict(slot=x['slot'],before=before,after=dict(x)))
assert len({x['reading'] for x in p['items']})==512
import csv
existing=list(csv.DictReader((R/'whitelist.csv').read_text(encoding='utf-8').splitlines()))
assert not ({x['reading'] for x in p['items']}&{x['reading'] for x in existing})
for s in p['sheets']:
 s['tiles']=[x for x in p['items'] if x['sheet']==s['sheet']]
 prefix=s['prompt'].split('Exact order:\n')[0]+'Exact order:\n'
 s['prompt']=prefix+'\n'.join(f'{i+1}. {x["word"]}: {x["scene"]}.' for i,x in enumerate(s['tiles']))
 (O/f'sheet{s["sheet"]:02}.prompt.txt').write_text(s['prompt'],encoding='utf-8')
(O/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(O/'name-review.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(corrected=len(changes),unique=512),ensure_ascii=False))
