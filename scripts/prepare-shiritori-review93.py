"""Prepare identity-checked requests and ImageGen batches; never selects by ID alone."""
import csv, hashlib, json
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'data/corrections/review93-2026-10-11'
OUT.mkdir(parents=True, exist_ok=True)
if (OUT/'ledger.json').exists():
    raise SystemExit('Applied review exists. Do not overwrite its baseline or reviewed generation record.')
spec = '''311|痛|いた|itami.png
344|一番|いちばん|complete-0347.png
345|一部|いちぶ|complete-0348.png
346|一面|いちめん|complete-0349.png
364|一指|いっし|pv-point.png
365|一周|いっしゅう|complete-0368.png
382|一致|いっち|complete-0385.png
385|一定|いってい|complete-0388.png
397|稲光|いなびかり|complete-0401.png
413|芋づる|いもづる|complete-0417.png
417|いやいや|いやいや|kirai.png
462|所謂|いわゆる|complete-0467.png
466|印|いん|complete-0471.png
486|引力|いんりょく|complete-0491.png
500|羽化|うか|complete-0505.png
502|うがい|うがい|complete-0507.png
524|嘘|うそ|complete-0531.png
526|嘘つき|うそつき|complete-0533.png
549|虚ろ|うつろ|complete-0557.png
580|埋め合わせ|うめあわせ|complete-0588.png
608|運転|うんてん|complete-0617.png
1432|機動|きどう|complete-0617.png
645|液|えき|complete-0654.png
648|液体|えきたい|complete-0654.png
710|婉曲|えんきょく|complete-0722.png
711|演技|えんぎ|complete-0723.png
724|遠心|えんしん|complete-0737.png
775|大きい|おおきい|complete-0792.png
776|大きさ|おおきさ|complete-0793.png
792|大幅|おおはば|complete-0810.png
799|公|おおやけ|complete-0818.png
803|お帰り|おかえり|complete-0822.png
812|お代わり|おかわり|complete-0831.png
819|置く|おく|complete-0838.png
829|教え|おしえ|ss-lecture.png
1567|教育|きょういく|ss-lecture.png
1574|教授|きょうじゅ|ss-lecture.png
831|お仕置き|おしおき|complete-0850.png
833|お支度|おしたく|complete-0852.png
863|落ちる|おちる|complete-0882.png
864|お使い|おつかい|complete-0883.png
872|おてんば|おてんば|nobinobi.png
888|劣る|おとる|make.png
894|驚く|おどろく|odoroku.png
896|お腹の空く|おなかのすく|onakanosuku.png
1692|空腹|くうふく|onakanosuku.png
911|お寝坊|おねぼう|chikoku.png
913|各々|おのおの|complete-0934.png
920|お話|おはなし|tsutaeru.png
937|溺れる|おぼれる|sukuu.png
938|おまけ|おまけ|omake.png
969|降りる|おりる|complete-0992.png
972|折る|おる|origami.png
979|お別れ|おわかれ|ss-farewell.png
1021|帰る|かえる|ss-farewell.png
1590|去る|さる|ss-farewell.png
984|恩恵|おんけい|complete-1007.png
1034|書き算|かきざん|complete-1058.png
1056|賢い|かしこい|aw-kenmei.png
1065|齧り付く|かじりつく|complete-0477.png
1175|噛む|かむ|complete-0477.png
1066|貸す|かす|ss-lend.png
1073|風|かぜ|complete-1097.png
1075|数える|かぞえる|complete-1099.png
1105|割入|かつにゅう|complete-1131.png
1170|紙飛行機|かみひこうき|kamihikouki.png
1173|噛みやん|かみやん|complete-1199.png
1195|通う|かよう|complete-1222.png
1198|空|から|complete-1225.png
1209|空っぽ|からっぽ|complete-1236.png
1215|借り|かり|ss-borrow.png
1220|借り暮らし|かりぐらし|ss-borrow.png
1217|仮|かり|complete-1244.png
1223|仮初め|かりそめ|complete-1250.png
1248|可愛い|かわいい|nikkori.png
1256|交わす|かわす|ss-communicate.png
1271|感覚|かんかく|complete-0048.png
1272|間隔|かんかく|complete-1301.png
1273|カンカン|かんかん|complete-0217.png
1307|監督|かんとく|ss-leader.png
1309|艱難辛苦|かんなんしんく|nintai.png
1372|着合う|きあう|complete-1401.png
1374|居合わせ|きあわせ|complete-1403.png
1375|起案|きあん|aw-kentou.png
1871|計画|けいかく|aw-kentou.png
1419|気体|きたい|complete-1448.png
1575|競争|きょうそう|complete-0620.png
1592|器用|きよう|complete-1624.png
1658|義務|ぎむ|sonchou.png
1690|空洞|くうどう|complete-1722.png
1691|空白|くうはく|complete-1723.png
1693|空欄|くうらん|complete-1725.png
1724|口利き|くちきき|complete-1757.png
1728|口封じ|くちふうじ|complete-1761.png
1733|屈身|くっしん|complete-1766.png
1739|駆動|くどう|complete-1772.png
1750|区別|くべつ|botan.png
1757|組|くみ|ss-class.png
1758|組合|くみあい|ss-union.png
1770|供養|くよう|complete-1804.png
1790|クリティカル|くりてぃかる|complete-0370.png
1881|計算|けいさん|complete-1916.png
1882|形式|けいしき|complete-1917.png'''
rows = list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')))
requests=[]
for line in spec.splitlines():
    oid,word,reading,file=line.split('|')
    matches=[(i,r) for i,r in enumerate(rows,1) if r['word']==word and r['reading']==reading and r['image_asset']=='assets/shiritori/'+file]
    assert len(matches)==1, (line,matches)
    actual,r=matches[0]
    requests.append(dict(requestedId=int(oid),resolvedId=actual,before=r))
assert len(requests)==103 and len({r['before']['image_asset'] for r in requests})==93
byid={r['requestedId']:r for r in requests}
edits={
311:dict(word='痛い',reading='いたい',meaning='からだのどこかに、つらい刺激や苦しさを感じるようす。',imagequery='痛い 腕',imagequery_en='Painful arm'),
344:dict(meaning='順位や順番が最初であること。また、程度がもっとも高いこと。'),
364:dict(meaning='一本の指のこと。指で何かを示す「指す」とは別の意味。',imagequery='一本の指',imagequery_en='One finger'),
413:dict(meaning='芋のつるのこと。つるを引くと芋がつながって出てくることから、一つが分かると関連することも次々に分かるたとえにも使う。'),
417:dict(meaning='したくないと思いながら、しぶしぶするようす。'),
462:dict(meaning='一般にそう呼ばれている、という意味の言葉。よく使われる呼び名や、典型的なものを示すときに使う。'),
466:dict(meaning='目じるしや、確かめるためのしるし。また、名前などを彫って押すはんこや、それを押した跡。',imagequery='印 はんこ 目印'),
549:dict(meaning='中がからで何もないこと。また、心がぼんやりして、表情に元気や気持ちが表れていないようす。'),
608:dict(meaning='機械を動かすこと。また、機械が動くこと。車などを操縦する意味でも使う。'),
711:dict(meaning='役になりきって、しぐさや表情、声などで場面を表すこと。'),
863:dict(meaning='物や人が、上から下へ移ること。支えを失って下へ動くことなど。'),
864:dict(meaning='人に頼まれて、買い物や用事をしに出かけること。'),
972:dict(meaning='物を曲げて重ねたり、曲げて切り離したりすること。紙を二つにたたむ、枝を折り取る、など。'),
984:dict(meaning='自然や社会の仕組み、人のはたらきなどから受ける、ありがたい助けや利益。'),
1034:dict(word='筆算',reading='ひっさん',meaning='数や式を紙などに書き、決まった手順で計算する方法。',imagequery='筆算',imagequery_en='Written arithmetic'),
1105:dict(word='割り込み',reading='わりこみ',meaning='順番を待たずに列の途中に入ったり、人の話などの途中に入り込んだりすること。',imagequery='列 割り込み',imagequery_en='Cutting in line'),
1195:dict(meaning='学校や職場など、同じ場所へくり返し行き来すること。'),
1220:dict(meaning='家や部屋を借りて、そこで生活すること。',imagequery='借家 暮らし',imagequery_en='Living in rented home'),
1273:dict(meaning='金属などを続けてたたいたときの、かたい音。また、とても腹を立てているようす。'),
1309:dict(meaning='さまざまな困難や、つらい苦しみ。'),
1372:dict(word='コーディネート',reading='こーでぃねーと',meaning='服などの色や形を、合うように組み合わせること。',imagequery='服 コーディネート',imagequery_en='Coordinating clothes'),
1374:dict(word='居合わせる',reading='いあわせる',meaning='あることが起きたとき、偶然その場所にいること。',imagequery='偶然 居合わせる',imagequery_en='Happen to be present'),
1419:dict(meaning='空気や二酸化炭素、水蒸気などのように、決まった形や体積を持たず、空間いっぱいに広がる物質の状態。白い湯気は水蒸気が冷えてできた細かい水滴。'),
1592:dict(meaning='手先で細かいことを上手にできたり、さまざまな物事をうまくこなせたりするようす。'),
1658:dict(meaning='立場や決まりによって、必ずしなければならないこと。日本国民には、子に普通教育を受けさせる義務、働く義務、税金を納める義務がある。'),
1733:dict(word='屈伸',reading='くっしん',meaning='体の関節を曲げたり伸ばしたりすること。絵では膝を曲げ伸ばしする運動。',imagequery='膝 屈伸運動',imagequery_en='Knee bends'),
1770:dict(meaning='亡くなった人などを思い、花や食べ物をそなえたり、祈ったりすること。'),
}
delete={1173:'「噛みやん」は一般的な日本語の単語でないため、指定に従って削除。画像は「噛む」へ移す。'}
# IDs here are request identities verified above, not unchecked row offsets.
# Each tuple: primary request; new filename or original filename; all identities to assign; scene.
stories=[
(345,None,[345],'A family cuts a whole birthday cake; a child takes only one small slice while the remaining cake is clearly visible. Show a part of a whole through a real scene.'),
(346,None,[346],'A child opens curtains and marvels at a garden entirely covered by fresh snow, from foreground to horizon; a whole surface blanketed with snow.'),
(364,'review93-one-finger.png',[364],'Close view of a child holding up exactly one index finger with the other four fingers folded, counting one. Entire hand visible, anatomically correct, not pointing at a distant object.'),
(365,None,[365],'A child on a bicycle completes one circuit of a circular park path, returning to the same starting bench where a parent waves. Path is visible as one continuous loop in a real park.'),
(382,None,[382],'A friendly forensic investigator kneels by a footprint in mud and holds a shoe beside it; distinctive zigzag sole exactly matches the muddy impression. Magnifying glass, no crime or distress.'),
(385,None,[385],'A grandparent and child watch a pendulum clock. Pendulum shown at evenly spaced swing positions with a small unobtrusive arc; steady rhythm at home, no disconnected diagram.'),
(413,None,[413],'Two clear narrative halves: left a child pulls a sweet-potato vine and several attached tubers emerge successively from soil; right a friendly investigator follows connected clues from one photo to another to solve a harmless mystery. Show literal vine and metaphor of linked discoveries, no words.'),
(417,'review93-reluctantly.png',[417],'A child reluctantly tidies scattered toys after a parent asks. Child IS doing the task, putting a block in a box, shoulders slumped, downturned mouth, unhappy but accepting; no refusal gesture.'),
(462,None,[462],'A friendly neighborhood inventor repairs a toy and builds a small wind-powered device in a garage. Neighbors point to him with admiring smiles and a shared speech bubble containing the short Japanese nickname「町の発明家」. Explain a common nickname people use, not a formal title; only this exact legible text.'),
(466,None,[466],'Three connected real-life views: a child marks a meeting spot on a map with a red mark; adult holds a carved name seal; the seal presses red ink onto paper leaving a clear stamp impression. Include physical seal and printed mark, no extra text.'),
(486,None,[486],'Beautiful outer-space scene of two spherical stars or planets in the same starry sky with soft mutual attraction lines, drifting slightly toward each other; small spaceship observes. Both bodies attract each other. No instructional labels or atom diagram.'),
(524,None,[524],'A child has just broken a blue vase with a ball. Nearby lies the ball and broken vase. Child points at an innocent seated cat and makes a speech bubble clearly showing that same CAT pushing the same vase, a false claim. Actual cat peaceful, adult skeptical.'),
(526,None,[526],'A boy repeatedly boasts unbelievable lies to skeptical friends: three speech bubbles show himself flying without wings, lifting a huge elephant, and riding a fish through the sky. Bubbles clearly show the same boy, exaggerated fanciful claims.'),
(549,None,[549],'A tired adult with an unmistakably vacant hollow expression sits looking into an empty cup: unfocused eyes, drooping posture, no smile, distracted gaze. A visibly empty open box nearby connects literal emptiness and emotional vacancy. Gentle, not frightening.'),
(1432,'review93-mobility.png',[1432],'A rescue crew rapidly changes its plan when a road is blocked by a fallen branch: one member points to an alternative route on a map, another immediately deploys a small nimble rescue vehicle toward the alternate path. Dynamic responsive action, safe scene, no ordinary car-driving lesson.'),
(775,None,[775],'A child planting trees looks up at an enormous mature tree beside a tiny new sapling. Human scale and natural setting make large height and breadth unmistakable.'),
(776,None,[776],'Two children measure the height and width of a cardboard box with a tape measure before choosing a box that fits a shelf. Clearly show measuring dimensions in a real packing scene.'),
(872,'review93-tomboy.png',[872],'A spirited GIRL with pigtails wearing shorts energetically climbs low playground climbing bars; cheerful active pose and playful muddy knees, a parent watches safely nearby. No boy as main subject.'),
(888,'review93-inferior.png',[888],'Two toy robots clean the same floor. A shiny robot moves quickly and has finished its neat clean area; a battered older robot crawls slowly with a visibly unfinished area, loose panel and small wobble marks. Compare machine performance, no human humiliation.'),
(894,None,[894],'A child opens a gift and is visibly startled: eyes very wide, eyebrows lifted high, mouth open in a round O, torso recoils, both hands lifted. A harmless toy springs from the gift, strong surprised expression, no smile.'),
(896,None,[896,1692],'A hungry child waits at a dining table with an EMPTY plate, clutching the stomach, furrowed brows, drooping shoulders and unhappy strained mouth. Cooking pot in the distant kitchen is not yet ready. No food in front of child, no delighted expression.'),
(911,'review93-overslept.png',[911],'A child sits upright IN BED in pajamas, suddenly realizing they overslept. Shocked worried face looks at an alarm clock showing late morning, bright sun through window, school bag by bed. Not a child arriving at school.'),
(913,None,[913],'Three children at one art table each work on their own distinct drawing with their own crayons; one draws flowers, one a boat, one a cat. Each individual acts separately in a shared believable scene.'),
(920,'review93-spoken-story.png',[920],'A parent tells a story aloud to two children seated nearby; mouth visibly speaking, friendly listening faces, a speech bubble shows a simple fairy-tale castle. No letters, envelopes, cards or written communication.'),
(937,None,[937,2974],'A child struggling in shallow water has a worried strained expression, splashes, and reaches for help; an adult on stable bank firmly pulls the child to safety by hand while another holds a flotation ring close. Clearly distress plus ongoing rescue, no injury, no submerged face or shocking danger.'),
(938,None,[938],'A shop counter with a large main chocolate bar and its wrapper; a tiny inexpensive plastic toy car in a separate little transparent bonus packet attached to the chocolate package. Child delighted by the small extra toy, chocolate visibly main purchase.'),
(969,None,[969],'A girl steps DOWN from a stationary bus onto a pavement, one foot firmly on sidewalk, the other on the lower bus step; handrail held, whole body and correctly formed feet visible. Bus door and steps coherent.'),
(984,None,[984],'A sunny farm with flourishing vegetables, a gentle irrigation stream and family enjoying the harvest. Sunlight, water and fertile soil visibly bring benefit; emphasize gifts of nature, not a person handing a gift.'),
(1056,'review93-clever.png',[1056],'A clever child solves how to cross a puddle without wet feet: places several stable stepping stones and tests the path carefully while a friend watches admiringly. Clear planning and good judgment, no adult cleaning a mess.'),
(1065,'review93-bite-apple.png',[1065],'Close view of a child biting directly into a large whole red apple, front teeth visibly meeting apple skin; apple much larger than one mouthful, small fresh bite mark. Not eating with a spoon.'),
(1075,None,[1075],'A child counts six apples one by one, index finger touching the next apple while the other hand records tally marks on paper. All apples and counting person visible, no abstract row of dots.'),
(1198,None,[1198],'A child opens a lunch box expecting lunch but finds it completely empty, looks puzzled and tips lid open toward viewer; companion starts offering a sandwich. Show an empty container as part of a story, not a labeled diagram.'),
(1209,None,[1209],'A child tilts a transparent cookie jar upside down after all cookies were eaten; absolutely nothing comes out. Surprised disappointed face, a few crumbs on table, jar clearly empty.'),
(1220,'review93-rented-home.png',[1220],'A family moves into a rented small house: landlord gives keys, moving boxes and modest sofa visible, family begins daily life inside. House on loan for living, not a child borrowing stationery.'),
(1217,None,[1217],'School event: a temporary reception desk made from a folding table and simple canopy stands in front of a permanent school entrance. Volunteers set it up and stack folding chairs, unmistakably temporary provisional setup.'),
(1223,None,[1223],'Fairy-tale princess at a ball under a short-lived magic spell: a clock approaches midnight, sparkling dress begins reverting into plain clothes at the hem and magical carriage fades toward a pumpkin outside. Transient condition, original storybook design, not a branded character.'),
(1248,'review93-cute-puppy.png',[1248],'An adorable small fluffy puppy tilts its head, round gentle eyes, tiny paws, soft ears; a child crouches nearby smiling fondly. Puppy is the main subject.'),
(1271,'review93-five-senses.png',[1271],'Five clearly separated vignettes of the same child: sees a colorful flower with eyes; listens to a ringing bell with ear; smells a flower with nose; tastes a strawberry with tongue; touches soft fabric with hand. All five senses explicitly visible, no labels.'),
(1272,None,[1272],'Children plant seedlings in a garden bed, using a small ruler to leave equal gaps between the plants. Main action is checking the distance between neighboring seedlings, real garden context.'),
(1273,'review93-kankan.png',[1273],'Two equal narrative halves: left a worker strikes a metal bell repeatedly with a small mallet, clear ringing vibration marks; right an angry child with furrowed brows, tight mouth and fists after a toy breaks. Show metallic ringing sound and intense anger, no text.'),
(1307,'review93-director.png',[1307],'Two coherent halves: film director beside camera giving actors instructions on a film set; sports coach beside a soccer field holding tactics clipboard and instructing team. Both directing people, cinema and sports explicitly visible.'),
(1309,None,[1309,2014,3373,4215],'A determined adult hiker perseveres through cold rain on a steep rocky uphill trail, shoulders strained under heavy backpack, face tired but resolute. Boots muddy, safe footing, wind and effort clear. Depict hardship, endurance and toughness without injury.'),
(1375,'review93-draft-proposal.png',[1375],'An office worker drafts a formal written proposal at a desk, several typed pages with neat headings and numbered sections, pen revising one page, computer and folder. Business documents are main focus, not models or childrens play.'),
(1871,'review93-planning.png',[1871],'Two friends plan a camping trip before leaving: study a paper calendar, map and checklist on a desk; a shared thought bubble shows tent and campsite they intend to visit. Plans on paper and in minds, not already building a model.'),
(1419,None,[1419],'Three real scenes integrated in one image: air being pumped into a transparent balloon; faint vapor mist above warm kettle, with heat source safe; bubbles of gas rising through sparkling water. Air inside balloon and bubbles are gases; no particle diagram, no solid smoke chunks.'),
(1575,'review93-competition.png',[1575],'Three distinct competitions in one coherent sports day collage: runners racing, children competing in a chess match, and two groups in a tug-of-war. Clearly broader competition beyond foot racing, friendly rivalry.'),
(1658,'review93-duties.png',[1658],'Three equally large connected scenes for Japanese civic duties: parent brings school-age child to a school gate (parent ensuring education); adult works in a workshop; adult pays tax at a government counter with a paper form and coins. No implying schoolchild has duty to work or pay taxes.'),
(1690,None,[1690],'A child opens a wooden matryoshka nesting doll into two halves, revealing its clearly hollow interior; smaller nesting doll sits beside it on table. Show actual inner cavity, not rectangular diagram.'),
(1691,None,[1691],'A child draws a colorful picture on paper but deliberately leaves a large white space for adding something later. Hand and colored crayons visible, the empty unmarked part of actual paper prominent, not an outlined answer box.'),
(1693,None,[1693],'A pupil at desk looks at a test answer sheet with a numbered problem and an EMPTY rectangular answer field; holds pencil ready to fill it. Minimal clear numerals and simple arithmetic such as 2+3=, no large arbitrary text.'),
(1733,None,[1733],'Two clear side-by-side poses of the same child performing ONLY knee bends: left upright with knees straight, right squat with knees bent and heels on ground, arms extended for balance. Simple arrow between poses, knees clearly visible, no forward bending or side stretching.'),
(1750,'review93-distinguish.png',[1750],'A child at kitchen table sorts red apples into one basket and green pear-shaped pears into a different basket after inspecting their shapes. Two types distinctly separated, no buttons.'),
(1790,'review93-critical.png',[1790],'An engineer at a control console urgently identifies a critical red flashing warning beside a dam water-level display and presses a safety control, another operator responds immediately. Serious pivotal situation with calm problem-solving, no animal fight, no disaster victims.'),
]
cropids=[397,500,502,580,645,710,724,792,799,803,812,819,829,831,833,979,1066,1073,1170,1215,1256,1724,1728,1739,1757,1758,1881,1882]
jobs=[]
for oid,file,uses,scene in stories:
    source=byid[oid]['before']['image_asset']
    jobs.append(dict(requestId=oid,file=file or Path(source).name,uses=uses,scene=scene,kind='new-story',source=source))
for oid in cropids:
    source=byid[oid]['before']['image_asset']
    uses=[r['requestedId'] for r in requests if r['before']['image_asset']==source]
    jobs.append(dict(requestId=oid,file=Path(source).name,uses=uses,kind='repair-framing',source=source,
       scene='Faithfully redraw the matching reference tile as one clean complete square illustration, preserving its main subject and meaning, removing ALL strips or fragments from neighboring pictures at bottom and sides, keeping hands and main objects fully visible.'))
plan=dict(date='2026-10-11',baselineCommit='b7986ad',beforeSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),requests=requests,edits=edits,delete=delete,jobs=jobs,
  reuse=[dict(requestId=1175,source='assets/shiritori/complete-1199.png',reason='指定に従い、削除する噛みやんの咀嚼場面を噛むへ移す。')])
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
write(OUT/'plan.json',plan)
groups=[]
for kind in ['new-story','repair-framing']:
    selected=[j for j in jobs if j['kind']==kind]
    for start in range(0,len(selected),16):
        tiles=selected[start:start+16];number=len(groups)+1
        style='Create a STRICT 4 by 4 grid contact sheet of 16 equally sized SQUARE tiles, row-major order. Warm Japanese childrens picture-book watercolor and clear line art, consistent gentle realistic anatomy. Each tile independent. Keep ALL content well within each tile with 7 percent margin on every edge. Pure white straight gutters at exact quarter boundaries. No tile numbers, captions, titles, borders, watermarks or extra panels. No words except explicitly requested in a tile. No bleed across tiles. Every main face and object complete.'
        if kind=='repair-framing':
            style+=' This is an EDIT of the attached reference grid: maintain each tile content and visual style and remove contaminated bottom/side neighbor fragments. Do not swap, merge, reorder or add subject matter.'
            ref=ROOT/'qa-output/request93'/f'reference-{number}.png';ref.parent.mkdir(parents=True,exist_ok=True)
            sheet=Image.new('RGB',(1024,1024),'white')
            for n,j in enumerate(tiles):
                with Image.open(ROOT/j['source']) as im:sheet.paste(im.convert('RGB').resize((256,256)),(n%4*256,n//4*256))
            sheet.save(ref)
        else:ref=None
        scenes=[]
        for n in range(16):
            scene=tiles[n]['scene'] if n<len(tiles) else 'Unused spare tile: a simple small green leaf centered on white background.'
            scenes.append(f'Tile {n+1} (row {n//4+1}, column {n%4+1}): {scene}')
        prompt=style+'\n'+'\n'.join(scenes)
        groups.append(dict(number=number,kind=kind,tiles=tiles,reference=str(ref) if ref else None,prompt=prompt,file=f'review93-2026-10-11-{number}.png'))
return_job=dict(requestId=1021,file='review93-return-home.png',uses=[1021],kind='new-story',source=byid[1021]['before']['image_asset'],scene='A child returns to their own home after school, stepping IN through the open front door with a schoolbag; parent inside welcomes child, shoes being removed at entry, familiar slippers waiting. Direction clearly toward home, not leaving home.')
jobs.append(return_job)
groups.append(dict(number=7,kind='new-story',tiles=[return_job],reference=None,columns=1,rows=1,file='review93-2026-10-11-7.png',prompt='One square Japanese childrens picture-book watercolor illustration, complete scene with clear anatomy, no captions or text, 7 percent safe margin around all content. '+return_job['scene']))
farewell_job=dict(requestId=1942,file='review93-depart-team.png',uses=[1942],kind='new-story',source='assets/shiritori/ss-farewell.png',scene='An adult has firmly decided to leave a sports team permanently. They return a team jersey and membership badge to the coach, wearing ordinary clothes and holding a packed personal bag. Serious resolute expression, other teammates watch sadly; the person then walks away from the clubhouse, no smiling daily see-you wave, no captions. Depict a decisive final parting, gentle and nonviolent.')
jobs.append(farewell_job)
groups.append(dict(number=8,kind='new-story',tiles=[farewell_job],reference=None,columns=1,rows=1,file='review93-2026-10-11-8.png',prompt='One square Japanese childrens picture-book watercolor illustration, complete scene with clear anatomy, no captions or text, 7 percent safe margin around all content. '+farewell_job['scene']))
write(OUT/'plan.json',plan)
write(OUT/'generation.json',groups)
print(json.dumps(dict(orders=len(requests),sourceImages=93,idMismatches=[r['requestedId'] for r in requests if r['requestedId']!=r['resolvedId']],imageJobs=len(jobs),groups=len(groups)),ensure_ascii=False))
