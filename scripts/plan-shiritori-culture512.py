"""Freeze culture vocabulary, familiarity levels, aliases and image-sheet order."""
import csv,collections,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/image-coverage/2026-10-19-culture512'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
base=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(base.decode('utf-8').splitlines()))
assert not (OUT/'plan.json').exists(),'Existing frozen plan must not be overwritten'
existing_readings={x['reading'] for x in rows};existing_words={x['word'] for x in rows}
fixes={'ふっこくじ':'ぶっこくじ','ふこうじおおどう':'ふきじおおどう','あんじんときよひめ':'あんちんときよひめ','うみのやまのいわれ':'うみのみずはなぜからい','らふぁえるろ':'らふぁえろ','あさがいちゅう':'あさいちゅう','かしょうほう':'ひなわじゅう','くらいもあ':'くれいもあ','つヴぁいへんだー':'つゔぁいへんだー','しずおかさしもの':'するがさしもの','びしゅうしっぽう':'おわりしっぽう','おおさかすずき':'おおさかなにわすずき'}
exclude={'やまんばのにしき','ならなしとり','こびとのおかゆ','じごくのそうべえ','きつねのでんわぼっくす','しなしゅう','うしこうび','えあろーぼう'}
sources={
 'tales':{'name':'国立国会図書館 昔話・童話資料','url':'https://www.ndl.go.jp/kaleido/entry/36/index.html'},
 'drinks':{'name':'国税庁 酒類の資料','url':'https://www.nta.go.jp/taxes/sake/index.htm'},
 'weapons':{'name':'The Metropolitan Museum of Art Arms and Armor','url':'https://www.metmuseum.org/departments/arms-and-armor'},
 'artists':{'name':'国立西洋美術館 所蔵作品検索','url':'https://collection.nmwa.go.jp/artizeweb/search_1_top.php'},
 'sites':{'name':'UNESCO World Heritage List','url':'https://whc.unesco.org/en/list/'},
 'crafts':{'name':'伝統的工芸品産業振興協会 工芸品一覧','url':'https://kougeihin.jp/craft/'},
 'hiroshima':{'name':'広島県教育委員会 広島県の文化財','url':'https://www.pref.hiroshima.lg.jp/site/bunkazai/'},
 'treasures':{'name':'文化庁 国指定文化財等データベース','url':'https://kunishitei.bunka.go.jp/bsys/index/'}}
pool=collections.defaultdict(list);rejected=[];category=''
for line in (OUT/'candidates.txt').read_text(encoding='utf-8').splitlines():
 if line.startswith('@'):category=line[1:];continue
 if not line or line.startswith('#'):continue
 a=line.split('|');reading=fixes.get(a[0],a[0]);word=a[1]
 meaning=a[3] if category=='tales' else a[2]
 if a[0] in exclude or '除外' in meaning or '扱わない' in meaning:
  rejected.append(dict(reading=reading,word=word,reason='表記・資料・対象範囲の再検討用。今回は未登録。'));continue
 if reading in existing_readings or word in existing_words:
  rejected.append(dict(reading=reading,word=word,reason='既存読みまたは表記。今回の新規512項目から除く。'));continue
 grade=int(a[2]) if category=='tales' else 5
 if category=='artists':scene='An explanatory still life about the work of '+word+': '+a[3]+'. Do not portray a person or copy a specific artwork. This is a contextual illustration, not a portrait or an authentic work.'
 elif category=='tales':scene='Original picture-book scene for the traditional/literary story '+word+'. '+meaning+' Show a recognizable central event using original character designs. Do not copy any publisher or film adaptation. No graphic harm.'
 elif category=='drinks':scene='Museum-like still life explaining '+word+'. '+meaning+' Show the characteristic drink, simple unbranded container, and relevant raw ingredient. No person drinking, no product labels.'
 elif category=='weapons':scene='Museum display of '+word+'. '+meaning+' Isolate the complete object in clear three-quarter view. Mythological and fictional subjects must look illustrative. No combat, no injuries, no instructions or cutaway mechanism.'
 else:scene='Accurate explanatory illustration of '+word+'. '+meaning+' Show distinguishing architecture, object, material or landscape. Not a photograph. Do not invent labels or mix nearby monuments.'
 pool[category].append(dict(reading=reading,word=word,meaning=meaning,grade=grade,category=category,scene=scene))
def spread(items,n):
 assert len(items)>=n,(len(items),n)
 return [items[round(i*(len(items)-1)/(n-1))] for i in range(n)] if n>1 else items[:1]
selected=[]
quotas=dict(tales=64,drinks=64,weapons=80,artists=64,sites=80,crafts=64,hiroshima=32,treasures=32)
for category,n in quotas.items():
 group=pool[category]
 if category=='artists':group=group[:40]+group[-24:]
 if category=='hiroshima':group=group[:16]+group[-16:]
 selected.extend(spread(group,n))
# Commonly used short and full names are separate readings for the SAME person.
ALIASES='''もね|くろーどもね|クロード・モネ
るのわーる|ぴえーるおーぎゅすとるのわーる|ピエール＝オーギュスト・ルノワール
どが|えどがーどが|エドガー・ドガ
せざんぬ|ぽーるせざんぬ|ポール・セザンヌ
ごっほ|ふぃんせんとふぁんごっほ|フィンセント・ファン・ゴッホ
ごーがん|ぽーるごーがん|ポール・ゴーガン
すーら|じょるじゅすーら|ジョルジュ・スーラ
しにゃっく|ぽーるしにゃっく|ポール・シニャック
ぴさろ|かみーゆぴさろ|カミーユ・ピサロ
れんぶらんと|れんぶらんとはるめんすぞーんふぁんれいん|レンブラント・ハルメンスゾーン・ファン・レイン
ふぇるめーる|よはねすふぇるめーる|ヨハネス・フェルメール
るーべんす|ぴーてるぱうるるーべんす|ピーテル・パウル・ルーベンス
ばんだいく|あんとにーばんだいく|アントニー・ヴァン・ダイク
べらすけす|でぃえごべらすけす|ディエゴ・ベラスケス
ごや|ふらんしすこごや|フランシスコ・ゴヤ
でゅーらー|あるぶれひとでゅーらー|アルブレヒト・デューラー
くらなは|るーかすくらなは|ルーカス・クラナハ
ぶりゅーげる|ぴーてるぶりゅーげる|ピーテル・ブリューゲル
ぷっさん|にこらぷっさん|ニコラ・プッサン
ろらん|くろーどろらん|クロード・ロラン
わとー|じゃんあんとわーぬわとー|ジャン＝アントワーヌ・ヴァトー
しゃるだん|じゃんばてぃすとしめおんしゃるだん|ジャン＝バティスト・シメオン・シャルダン
だびっど|じゃっくるいだびっど|ジャック＝ルイ・ダヴィッド
どらくろわ|うじぇーぬどらくろわ|ウジェーヌ・ドラクロワ
くーるべ|ぎゅすたーぶくーるべ|ギュスターヴ・クールベ
みれー|じゃんふらんそわみれー|ジャン＝フランソワ・ミレー
こーろー|じゃんばてぃすとかみーゆこーろー|ジャン＝バティスト・カミーユ・コロー
ほるばいん|はんすほるばいん|ハンス・ホルバイン
からばっじょ|みけらんじぇろめりーじだからばっじょ|ミケランジェロ・メリージ・ダ・カラヴァッジョ
てぃつぃあーの|てぃつぃあーのべちぇっりお|ティツィアーノ・ヴェチェッリオ
ぼってぃちぇり|さんどろぼってぃちぇり|サンドロ・ボッティチェリ
らふぁえろ|らふぁえろさんつぃお|ラファエロ・サンツィオ'''
for line in ALIASES.splitlines():
 short,reading,word=line.split('|');target=next(x for x in selected if x['reading']==short)
 assert reading not in existing_readings and word not in existing_words
 selected.append(dict(target,reading=reading,word=word,aliasOf=short,meaning=target['meaning']+'「'+target['word']+'」と同じ人物の名前。'))
assert len(selected)==512,len(selected)
assert len({x['reading'] for x in selected})==512
assert all(re.fullmatch('[ぁ-ゖー]+',x['reading']) for x in selected)
# Attach JMdict evidence when available; proper nouns retain the category authority.
jmdict=json.loads(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
by_reading=collections.defaultdict(list)
for e in jmdict['words']:
 for k in e.get('kana',[]):by_reading[k['text']].append(e)
items=[];generated=[]
for offset,x in enumerate(selected):
 ident=len(rows)+offset+1
 x.update(id=ident,level=min(x['grade'],3),filename=f'culture512-word-{ident}.png',credit='AI生成イラスト',
  lexicalSource=dict(primaryReference=sources[x['category']],entries=by_reading.get(x['reading'],[]),lookupWord=x['word']),
  meaningReason='指定分野の語を選定し、対象・所在地・作者・作品を区別して独自の日本語で説明。',
  ageReason=('知名度と、児童向け再話・読み聞かせで接する見込みによる編集上の判断。実測した認知率ではない。レベル'+str(x['grade'])) if x['category']=='tales' else 'ユーザー指定に従い、酒・武器兵器・文化芸術の発展語をレベル5とする。',
  imageReason=('芸術家の仕事・画材・題材の説明イラスト。本人の肖像や本人の作品の複製ではない。' if x['category']=='artists' else '当該語義を表す独自イラスト。')+x['scene'])
 if not x.get('aliasOf'):
  index=len(generated);x.update(sheet=index//16+1,tileIndex=index%16+1);generated.append(x)
 items.append(x)
for x in items:
 if x.get('aliasOf'):
  target=next(y for y in items if y['reading']==x['aliasOf']);x.update(filename=target['filename'],sharedWithId=target['id'],sheet=target['sheet'],tileIndex=target['tileIndex'])
assert len(generated)==480
save(OUT/'sources.json',sources);save(OUT/'excluded-candidates.json',rejected)
(OUT/'registration-baseline.csv').write_bytes(base)
save(OUT/'plan.json',dict(batch=OUT.name,baselineRows=len(rows),baselineSha256=hashlib.sha256(base).hexdigest(),items=items))
prefix='''Edit the attached equal-size 4 by 4 template. Paint EXACTLY sixteen separate vocabulary illustrations in its white cells, row-major left to right then top to bottom. Preserve 2048 by 2048 canvas dimensions and ALL FIVE horizontal and FIVE vertical continuous pure MAGENTA #ff00ff lines including the outer frame at their exact positions and thickness. Do not erase, move, cover or redraw grid lines. Magenta is ONLY for lines; no pink, violet or purple in artwork. Use each cell generously. Entire subjects, architecture and shadows stay within their own cells. Warm clear watercolor picture-book / educational museum style. Accurate subject structures. NO TEXT, labels, letters, numbers, watermarks or extra panels. No imitation of copyrighted adaptations or modern artists' styles. Exact cell order:\n'''
sheets=[]
for n in range(1,31):
 group=[x for x in generated if x['sheet']==n]
 prompt=prefix+'\n'.join(f'{i+1}. {x["scene"]}' for i,x in enumerate(group))
 (OUT/f'sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8')
 sheets.append(dict(sheet=n,tiles=group,prompt=prompt))
save(OUT/'sheets.json',sheets)
print(json.dumps(dict(total=len(items),images=480,aliases=32,byCategory=dict(collections.Counter(x['category'] for x in items)),grades=dict(collections.Counter(x['grade'] for x in items))),ensure_ascii=False))
