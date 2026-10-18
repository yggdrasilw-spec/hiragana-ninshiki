"""Freeze 64 reviewed meanings and image scenes; never overwrite dictionary data."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-request25'
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# reading | word | independent Japanese explanation | grade | scene
RAW='''めんこ|めんこ|厚い紙などの札を地面に打ちつけて、相手の札を裏返す遊び。また、その札。|2|Two children playing Japanese menko with thick round and rectangular illustrated cardboard disks on the ground; one striking a disk downward.
うしがえる|ウシガエル|牛のような低い声で鳴く大型のカエル。北アメリカ原産で、日本にも広がっている。|3|Accurate American bullfrog beside pond: olive brown large stout body, large round tympanum behind eye, no raised dorsolateral ridges down back.
めっき|めっき|物の表面を別の金属の薄い膜でおおうこと。さびを防いだり、見た目を整えたりする。|3|Cutaway metal spoon with dull grey metal core and very thin shiny silver outer coating; magnifying glass emphasizes the thin outer layer, no text.
すもも|スモモ|バラ科の木。また、その木になる、丸くて赤色などの皮をもつ甘酸っぱい果物。|1|Japanese plums: reddish round fresh fruit with natural central seam, one halved revealing yellow flesh and a single stone, leafy twig.
ねばり|粘り|物がくっついたり、のびたりする性質。また、簡単にあきらめずに続ける力。|2|Sticky rice cake stretched gently between two chopsticks showing elastic sticky strands, clear close-up.
とんねる|トンネル|山や地面などを掘って通した、列車や車、人などが通る道。|1|Passenger train passing out of a stone-lined railway tunnel through a green hill, cutaway glimpse of passage.
うんざり|うんざり|同じことが続いたり、いやなことが多かったりして、もういやだと思う様子。|2|Child with weary fed-up expression facing a repetitive pile of identical tangled cords, cheeks resting in hands, no letters.
りもーと|リモート|遠く離れた場所から、通信などを使って行うこと。|2|Two people in separate distant rooms communicating through laptops, small connecting dotted line between rooms.
うむらうと|ウムラウト|ドイツ語などで母音が変化すること。また、ä・ö・üなどの字の上につける二つの点。|4|DIAGRAM: umlaut
こんすたんてぃのーぷる|コンスタンティノープル|今のトルコのイスタンブールにあたる都市の昔の名前。東ローマ帝国の都だった。|4|Historical reconstruction of Byzantine Constantinople: fortified sea walls, harbor and domed Hagia Sophia without Ottoman minarets, clearly a historical city illustration.
でみぐらすそーす|デミグラスソース|肉のだしなどを使って煮つめた、こくのある茶色いソース。洋食に使う。|2|White gravy boat pouring glossy rich dark brown demi-glace sauce onto hamburger steak on plate.
くみたいそう|組体操|二人以上で体を支え合ったり、動きを合わせたりして行う体操。|2|Two children seated back-to-back on a gym mat doing a low balanced partner gymnastics pose, all feet grounded, anatomically correct.
きみがよ|君が代|日本の国歌の名前。入学式や卒業式、スポーツの式典などで歌われる。|2|School ceremony chorus singing with a Japanese flag on a pole beside stage; white flag with centered red circle, no lyrics or notation.
びら|ビラ|知らせや広告などを書いて配ったり、貼ったりする紙。|2|Person handing out small illustrated announcement leaflets, one attached to noticeboard, only pictures and abstract lines no letters.
るっくす|ルックス|人の顔立ちや服装など、外から見た姿や見た目。|3|Person looking at their face and clothing in a full-length mirror, neutral everyday appearance, no beauty ranking.
るろう|流浪|住む場所を定めずに、あちこちをさまよい歩くこと。|4|Traveler with shoulder bag walking along winding road past several distant villages, conveys wandering from place to place.
くびながりゅう|首長竜|恐竜がいた時代の海にすんだ爬虫類の仲間。四つのひれがあり、恐竜とは別の仲間。|3|Accurate long-necked plesiosaur underwater in side three-quarter view, small head, streamlined body, FOUR paddle flippers and short tail, neck gently forward, no legs or dinosaur spines.
みんく|ミンク|水辺にすむイタチの仲間の動物。細長い体と短い足をもち、泳ぎが得意。|4|Mink at stream edge: slender dark brown mustelid, small rounded ears, short legs, tapered furry tail and small white chin patch.
くろうと|玄人|ある仕事や技術について、専門の知識や高い腕前をもつ人。|3|Expert adult woodworker skillfully planing a neat wooden board in workshop, finished fine wooden objects nearby.
しぼう|脂肪|体にたくわえられてエネルギーのもとになったり、体温を保ったりする物質。食べ物にも含まれる。|3|Non-graphic educational skin cutaway: thin skin surface, soft yellow fatty layer underneath, muscle below; emphasize yellow fat layer with magnifying circle, no text.
しぼう|志望|自分が将来なりたいことや、進みたい学校・仕事などを望むこと。|3|Child thinking about becoming a veterinarian, thought bubble shows same person gently caring for a cat with stethoscope.
しぼう|死亡|人や動物が死ぬこと。命が終わること。|3|Respectful quiet remembrance: empty picture frame with simple silhouetted elderly portrait beside white flowers, family standing quietly, no corpse or injury.
らぐ|ラグ|部屋の床の一部分に敷く敷物。|2|Small woven rectangular rug on wooden living room floor in front of sofa, entire rug visible.
らぐ|ラグ|二つの出来事の間に生じる時間のずれや遅れ。ゲームや通信でも使う言葉。|3|Two adjacent screens showing same ball movement: left ball has reached goal while right ball remains behind, small clock between screens, no letters.
ぷーま|プーマ|南北アメリカにすむ大型のネコの仲間。ピューマやクーガーとも呼ばれる。|4|Accurate adult puma cougar on rocky American hillside: plain tawny coat, round ears, long tail, no mane, no spots, no black panther.
ぷーま|プーマ|スポーツ用の靴や服などをつくる、ドイツで生まれたブランドの名前。|5|CARD: PUMA
ぐりこ|グリコ|江崎グリコが販売する、キャラメル菓子の商品名。|5|CARD: グリコ
ししまい|獅子舞|獅子の頭をかたどったかぶり物をつけて踊る、伝統的な芸能。|2|Japanese shishimai dancer wearing red wooden lion head with movable jaw and green cloth with white curls; dancer feet underneath.
こまいぬ|狛犬|神社などの入り口で、左右に置かれることが多い、獅子や犬に似た守りの像。|2|Pair of Japanese stone komainu on pedestals flanking shrine path, curly lion-dog manes, one mouth open and one mouth closed, no real dogs.
べーごま|ベーゴマ|ひもを巻いて回し、ぶつけ合って遊ぶ小さな金属のこま。|2|Two small squat cast-metal Japanese beigoma tops spinning on a stretched cloth arena with winding string beside them, no long wooden stems.
おはじき|おはじき|平たい小さな玉を指ではじいて遊ぶ遊び。また、その玉。|1|Flattened transparent colored glass ohajiki disks on table, child's fingertip flicking one disk toward another.
たけとんぼ|竹とんぼ|竹などで作った羽根に棒をつけ、両手でもんで回すと飛ぶおもちゃ。|1|Traditional bamboo dragonfly toy with horizontal two-bladed bamboo propeller and long thin vertical stem, child's palms spin stem.
ひきがえる|ヒキガエル|ずんぐりした体と、いぼのようなでこぼこのある皮膚をもつカエルの仲間。|3|Stocky Japanese toad on forest floor, dry bumpy brown skin, squat posture, clear raised parotoid glands behind eyes.
かじかがえる|カジカガエル|山あいの川などにすみ、雄が美しい声で鳴くカエル。|4|Kajika frog Buergeria buergeri resting on stream rock: flattened grey mottled body and broad toe pads, rushing clear water.
きんめっき|金めっき|物の表面を金の薄い膜でおおうこと。|3|Metal pendant in cross section with thin golden outer coating surrounding grey metal core, magnifying lens shows coating.
ぎんめっき|銀めっき|物の表面を銀の薄い膜でおおうこと。|3|Silver-plated serving spoon with thin shiny silver surface over darker core shown in small enlarged cutaway, no text.
とたん|トタン|鉄の板に亜鉛をめっきした材料。屋根や壁などに使う。|3|Corrugated galvanized grey metal sheet with small shed roof made from matching sheet, metallic zinc texture.
ぷるーん|プルーン|スモモの仲間の果物。また、その実を乾かしたもの。|2|Purple European plums beside wrinkled dark dried prunes in small bowl, one fresh fruit halved with amber flesh and single stone.
ねばりけ|粘り気|物がくっついたり、ねばねばしたりする性質。|2|Chopsticks lifting sticky natto beans from bowl with visible thin sticky strands.
ねんせい|粘性|液体などが流れにくく、ねばる性質。|4|Two clear containers side by side, water pours quickly and honey drips slowly from tilted spoons, no text.
ねばりづよさ|粘り強さ|難しいことでも、簡単にあきらめずに続ける力。|2|Child patiently retrying a challenging jigsaw puzzle, several attempts indicated by earlier incomplete pieces, focused hopeful expression.
ずいどう|隧道|トンネルのこと。山や地面などを掘って通した道。|4|Stone masonry pedestrian tunnel through hillside with daylight visible at far end and hiker at entrance.
りもーとわーく|リモートワーク|会社などの仕事場から離れた場所で、通信を使って仕事をすること。|3|Adult working from home at laptop with office colleagues visible as small faces on video meeting screen, ordinary home desk.
てれわーく|テレワーク|通信を使い、会社の事務所などから離れた場所で働くこと。|3|Adult doing office tasks on laptop in a community satellite work room, distant office building visible through inset, no text.
えんかく|遠隔|場所が遠く離れていること。|3|Two houses far apart across wide valley with people waving from each side, visible long separation.
おんらいんかいぎ|オンライン会議|インターネットを使い、離れた場所にいる人どうしが話し合う会議。|3|Laptop screen with four adult participants in video call grid, person listening at desk, no readable interface text.
いすたんぶーる|イスタンブール|ヨーロッパとアジアにまたがる、トルコの大きな都市。ボスポラス海峡に面している。|3|Modern Istanbul skyline with Bosphorus water, ferry, suspension bridge and mosques in distance, city on both shores.
びざんつ|ビザンツ|後にコンスタンティノープルとなった、古代の都市の名前。|4|Historical imaginative reconstruction of ancient Greek Byzantium harbor on Bosphorus with classical stone buildings and sailing boats, no later Ottoman buildings.
ほわいとそーす|ホワイトソース|小麦粉をバターなどでいため、牛乳などでのばした白いソース。|2|Saucepan of creamy white sauce with whisk, milk pitcher, butter and bowl of flour beside it.
べしゃめるそーす|ベシャメルソース|小麦粉をバターでいため、牛乳でのばして作る白いソース。ホワイトソースの一種。|4|White bechamel sauce being whisked in saucepan with milk butter flour nearby, creamy thick texture.
ぶらうんそーす|ブラウンソース|小麦粉を茶色くいためたものや肉のだしなどを使う、茶色いソース。|3|Brown roux in pan beside stock pitcher and finished brown sauce in gravy boat, recognizable cooking ingredients.
しぼう|子房|花のめしべの根元にあるふくらんだ部分。中に胚珠があり、受粉後に実になることが多い。|3|Accurate simple longitudinal cutaway of a flower: petals above, central pistil with style leading down to a swollen green ovary containing small ovules; magnifying inset emphasizes ovary and ovules, no text.
こっか|国歌|国を代表する歌。日本の国歌は「君が代」。|2|International sports ceremony with three separate flagpoles and respectful audience beside musicians, no podium medals or written lyrics.
さざれいし|さざれ石|小さな石。細かな石のこと。|3|Close-up of several small natural pebbles scattered across sandy stream bed, clearly tiny separate stones, no giant boulder.
えるもさうるす|エラスモサウルス|恐竜がいた時代の海にすんだ首長竜の仲間。とても長い首と四つのひれをもつ。|4|Accurate Elasmosaurus underwater, very long neck about half body length, small head, compact torso, FOUR flippers, short tail, no dinosaur legs.
いたち|イタチ|細長い体と短い足をもち、小動物などを食べる動物の仲間。|2|Small Japanese weasel with slender reddish-brown body, pale throat and belly, short legs, short furry tail, standing on woodland ground.
てん|テン|イタチの仲間の動物。森林などにすみ、ふさふさした長い尾をもつ。|4|Japanese marten Martes melampus in winter: golden brown fur, pale face, rounded ears, bushy long tail, on forest branch.
しろうと|素人|ある仕事や技術について、専門の知識や経験がまだ少ない人。|3|Beginner adult learning pottery from teacher, simple uneven pot and careful attentive expression, kind respectful scene.
じゅくれん|熟練|長く練習や経験を重ねて、仕事や技術が上手になること。|3|Experienced potter shaping a symmetrical clay pot skillfully on pottery wheel, several well-made bowls nearby.
しぼうぶん|脂肪分|食べ物などに含まれている脂肪の成分や、その量。|3|Butter, cooking oil and milk arranged on kitchen counter with magnifying inset of golden fat droplets, no numbers or labels.
らぐまっと|ラグマット|床の一部分に敷く、小さめの敷物。|2|Small oval woven rug mat beside bed on wooden floor, whole mat visible.
たいむらぐ|タイムラグ|二つの出来事の間に生じる時間のずれや遅れ。|3|Person waves in front of webcam but remote screen still shows hand down, two separate rooms with small clock inset, no letters.
ししがしら|獅子頭|獅子舞などで使う、獅子の頭をかたどったかぶり物。|3|Close-up isolated traditional Japanese red lacquer shishigashira lion mask with golden eyes, green ears, white mane and movable jaw.
かぐら|神楽|神社の祭りなどで、神にささげるために行う音楽や舞。|3|Traditional Japanese kagura dancer with white robes and red hakama holding bells and folding fan on shrine stage with flute and drum musicians, no lion mask.'''
base=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(base.decode('utf-8').splitlines()))
raw=[line.split('|') for line in RAW.splitlines()]
assert len(raw)==64,len(raw)
data=json.loads(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
norm=lambda s:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
by_reading={}
for entry in data['words']:
 for reading in {norm(k['text']) for k in entry.get('kana',[])}:by_reading.setdefault(reading,[]).append(entry)
items=[];generated=[]
for offset,(reading,word,meaning,grade,scene) in enumerate(raw):
 # Correct the Japanese reading to match the established animal name.
 if word=='エラスモサウルス':reading='えらすもさうるす'
 ident=len(rows)+offset+1;grade=int(grade)
 assert not any(x['reading']==reading and x['word']==word for x in rows),(reading,word)
 matches=by_reading.get(reading,[])
 exact=[e for e in matches if any(k['text']==word for k in e.get('kanji',[]))+any(k['text']==word for k in e.get('kana',[]))]
 candidates=exact or matches
 item=dict(id=ident,reading=reading,word=word,meaning=meaning,grade=grade,level=min(grade,3),scene=scene,filename=f'request25-word-{ident}.png',
  lexicalSource={'name':'JMdict','date':data['dictDate'],'entries':candidates},
  meaningReason='指定語と関連語の語義を個別に確認し、子ども向けに独自に説明した。'+('同じ読みの別の意味と区別する。' if reading in ('しぼう','らぐ','ぷーま','こっか','てん') else ''),
  ageReason={1:'低学年の生活や遊びで触れる具体的なもの。',2:'中学年の生活・学校行事や言葉の学習で理解できる。',3:'高学年の理科・社会・読書や一般的な社会経験で理解する意味。',4:'専門的または一般児童にはなじみが薄いため発展レベル。',5:'商品やブランドの個別名のため固有名詞レベル。'}[grade],
  imageReason='この語義のための専用画像。'+scene,
  distinctSenseReason='既存および今回の同じ読みとは語義が異なる。国歌は国家と異なり、テンは点・天と異なる。',
  credit='プログラム生成図' if scene.startswith('DIAGRAM') else '独自文字カード（外部検索なし）' if scene.startswith('CARD') else 'AI生成イラスト')
 if item['credit']=='AI生成イラスト':
  index=len(generated);item.update(sheet=index//16+1,tileIndex=index%16+1);generated.append(item)
 items.append(item)
assert len(generated)==61
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'registration-baseline.csv').write_bytes(base)
save(OUT/'plan.json',dict(batch='2026-10-19-request25',baselineRows=len(rows),baselineSha256=hashlib.sha256(base).hexdigest(),items=items))
prefix='''Edit the attached equal-size 4 by 4 template. Paint EXACTLY sixteen separate vocabulary illustrations in the white cells, row-major left to right then top to bottom. Preserve canvas dimensions and ALL FIVE horizontal and FIVE vertical continuous pure MAGENTA #ff00ff lines including outer frame, at exact positions and thickness. Do not move, erase or paint over lines. Magenta ONLY for lines; no pink, purple or violet in artwork. Use each cell generously with no required blank margins. Entire artwork and shadows stay inside own cell. Warm clear watercolor picture-book illustrations, accurate anatomy. No text, captions, letters, numbers, watermark or extra panels. Subjects in exact order:\n'''
sheets=[]
for n in range(1,5):
 group=[x for x in generated if x['sheet']==n];tiles=[dict(x) for x in group]
 while len(tiles)<16:tiles.append(dict(filename=f'request25-unused-sheet{n}-slot{len(tiles)+1}.png',scene='A small wooden toy spinning top, unused spare illustration.'))
 prompt=prefix+'\n'.join(f'{i+1}. {x["scene"]}' for i,x in enumerate(tiles))
 (OUT/f'sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8');sheets.append(dict(sheet=n,tiles=tiles,prompt=prompt))
save(OUT/'sheets.json',sheets)
print(json.dumps(dict(rows=len(items),generated=len(generated),diagrams=3,missingLexical=[x['word'] for x in items if not x['lexicalSource']['entries']]),ensure_ascii=False))
