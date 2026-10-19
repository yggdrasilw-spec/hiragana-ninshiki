"""Persist the assistant's completed visual review, bound to adopted source hashes."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'data/image-coverage/2026-10-19-nature512'
p=json.loads((O/'plan.json').read_text(encoding='utf-8'))
notes={
1:'元素の物質・用途の説明図。半導体ウェハーの罫線色に近い反射を修正。',
2:'金属試料、密閉した臭素、用途の品を対応。テクネチウムは検査の概念図。',
3:'ヨウ素の黒い結晶に修正。各金属と用途の対応を確認。',
4:'希土類等の試料と用途の概念図。光るものは蛍光体・装置を表す。',
5:'水銀の液体、ビスマスの階段状結晶、放射性元素の密閉容器を区別。罫線の映り込みを修正。',
6:'人工元素は合成研究装置の概念図。実在する巨視的な金属塊の再現とは扱わない。',
7:'人工元素の研究イメージと、伝承上の天使の独自想像図。',
8:'伝承上の悪魔の独自想像図。現代作品のキャラクターの再現ではない。',
9:'伝承の想像図と、耳飾りの留め方・部品の違いを確認。',
10:'装飾品の用途・形・留め方と対応。肖像カメオ等は一般的な独自意匠。',
11:'指輪・髪留め等の機構と区別。アレキサンドライトは光源による色の違いの説明図。',
12:'ベリル・トルマリン・ガーネット等の代表的な形と色。ロードライトの色を深い赤に修正。',
13:'鉱物・宝石名と代表色・結晶形・キャッツアイ・スター効果を照合。',
14:'オパール・装飾石の模様、透明感、内部模様を区別。',
15:'金属鉱物・硫化鉱物・鉄鉱物の代表的な光沢と形。斑銅鉱の罫線色に近い反射を修正。',
16:'銅鉱物・炭酸塩・硫酸塩の代表形。鉱物同定写真ではない。',
17:'雲母の層、長石の塊、かんらん石、柱状・板状の鉱物を区別。',
18:'輝石等の結晶、玉髄・蛋白石・水晶の形と模様。',
19:'ヤドクガエルの背中と脚の配色、帯・斑点・縦線を種別の指示と照合。地域変異の一例。',
20:'ヤドクガエルの配色と模様、末尾のシシバナヘビの反った鼻を確認。',
21:'キングヘビ・ミルクヘビ等の帯模様、ナメラ類の体型と模様を区別。',
22:'ナメラ・水生ヘビ・ボア等の体型、模様、触手や尾の特徴を確認。',
23:'ニシキヘビ類の体型・模様、カブトトカゲの目の赤い輪、アオジタの舌を区別。',
24:'スキンク・ヨロイトカゲ・オオトカゲのうろこ、尾、色と模様を区別。',
25:'ヒルヤモリ等の模様と体型。タマオヤモリ二種の不正な房状の尾を細かなうろこと一つの末端の玉に修正。',
26:'リクガメとニオイガメ等の甲羅の形、模様、頭の色を照合。',
27:'水棲ガメの甲羅と頭の線、マタマタの扁平な頭と鼻、長い首等を確認。',
28:'カメの甲羅と頭の模様、サメの頭・ひれ・配色、ツキノワグマの胸、グリズリーの毛色。全身と等寸グリッドを修正。',
29:'クマ・イヌ科・大型ネコ・カイマンの体型、模様、耳・口先を区別。亜種・別名は意味欄で区別。',
30:'ワニの口先、イモガイの殻模様、クラゲの傘と触手、魚のひれととげ等を確認。',
31:'ウニのとげ、サソリの尾、クモの体と脚、昆虫の六脚を確認。',
32:'ムカデは胴の一部が落ち葉の下に隠れた自然場面として採用。脚対数の全体図として使わない。リンは宝石状の結晶から赤褐色の無定形粉末に修正。',
33:'定番のヤモリ・リクガメ・ハコガメ・スッポンについて種別の体型・模様・皮膚・甲羅を確認。',
34:'スッポン類の甲羅・鼻・ひれ状の脚、トカゲモドキ類、クビワトカゲ、トゲオアガマの形と模様を確認。'}
edits={
1:'In cell 9 ONLY, change the silicon wafer colors to blue, cyan, green and gold with NO pink, magenta, red-violet or purple. Remove every magenta reflection from artwork in all cells. Preserve every object and the grid exactly.',
3:'In cell 8 ONLY, make the iodine crystals dark charcoal-black with subtle deep navy highlights, no purple/magenta/pink facets. Remove every magenta reflection from artwork in all cells. Keep all other educational subjects and grid unchanged.',
5:'Remove every small magenta/pink reflection or stray magenta line from the metal container bases and artwork inside all sixteen cells, especially cell 2 and the last row. Replace those reflections with neutral gray/silver. Keep the magenta divider grid exactly intact, preserve all objects, their positions and their shapes.',
12:'In cell 15 ONLY, recolor the rhodolite garnet to deep dark wine-red, with red, maroon and neutral white highlights. Absolutely NO saturated pink, fuchsia or magenta facets. Preserve the educational object identity and all other stones. Remove any stray magenta inside cells; keep magenta grid lines intact.',
15:'In cell 6 ONLY, adjust the bornite tarnish colors to deep blue, cyan, gold and subdued dark violet; absolutely no magenta, pink or fuchsia patches. Preserve bornite rough texture, all other minerals, cell order, and exact magenta grid.',
25:'Correct ONLY the tails of the knob-tailed geckos in cells 9 and 10. Their tails must NOT look like raspberries, bunches of grapes, clustered spheres, or cauliflower. Nephrurus wheeleri in cell 9: a short relatively slender tapered tail with fine granular skin ending in ONE TINY round terminal knob. Nephrurus levis in cell 10: a single short plump tapering carrot-like tail with fine granular skin and ONE TINY round terminal knob. Keep the gecko bodies, their limb anatomy and all other fourteen cells unchanged. Preserve all straight magenta dividers.'}
generation_notes={
'2-8':'IMPORTANT: absolutely no magenta, pink or purple anywhere inside artwork, even iridescence, reflections or minerals. Blue-green is allowed. Magenta ONLY on divider lines.',
'9-16':'Important color constraint: absolutely no saturated magenta or magenta reflections inside cells. No colored grid glow or reflected divider lines. Gemstone pinks should be pale peach, violets blue-violet. Pure magenta is reserved for the straight divider lines.',
'17-24':'Important: no saturated magenta inside artwork, including iridescent reflections. Magenta divider lines must not cast reflections. Natural pinks should be pale salmon; violet should be dark blue-violet. For animals depict the EXACT scientific species and distinguishing pattern described; do not blend neighboring animals.',
'25-34':'Critical: Keep accurate species anatomy and stated identifiers, four legs for reptiles except snakes, exactly eight legs for spiders, six for insects. No saturated magenta inside cells and no grid reflections. Magenta reserved only for straight separators.'}
reviews=[]
for n in range(1,35):
 s=json.loads((O/f'sheet{n:02}-staged.json').read_text(encoding='utf-8'));source=R/s['source'];assert s['sha256']==hashlib.sha256(source.read_bytes()).hexdigest()
 base=(O/f'sheet{n:02}.prompt.txt').read_text(encoding='utf-8');extra=next((v for k,v in generation_notes.items() if int(k.split('-')[0])<=n<=int(k.split('-')[1])),'')
 full=base+'\n'+extra
 if n in edits:full+='\nTARGETED EDIT (preserve exact grid and subjects): '+edits[n]
 if n==28:full+='\nREGENERATE WITH TEMPLATE: exact equal-sized four rows and four columns. Show every shark entire, including tail and every fin inside its cell. Keep all five horizontal/vertical magenta divider lines in their exact template positions.'
 if n==32:
  full+='\nREJECTED EDIT: Attempted 21 leg pairs; complete figures were still too short and were not adopted.\n'
  full+=(O/'sheet32-v3.edit.prompt.txt').read_text(encoding='utf-8')+'\n'+(O/'sheet32-v4.edit.prompt.txt').read_text(encoding='utf-8')
 source.with_suffix('.prompt.txt').write_text(full,encoding='utf-8')
 reviews.append(dict(sheet=n,sha256=s['sha256'],source=s['source'],passed=True,approvedSlots=list(range(1,17)),reviewType='assistant-visual-content-review',notes=notes[n],scope='教育用の説明イラスト。写真・標本の同定用画像ではない。'))
for x in p['items']:
 if x.get('atomicNumber',0)>=99:x['meaning']+='画像は研究装置のイメージ。'
 if x['reading'] in ['とびずむかで','あおずむかで','たいわんおおむかで']:x['imageReason']='頭・触角・体色と最後の脚を確認。胴の中央は落ち葉で隠れた自然場面。脚対数の全体を説明する図ではない。'
 if x['reading']=='りん' and x['category']=='elements':x['imageReason']='密閉容器内の赤褐色の無定形の赤リンを描く。透明な宝石状の結晶にはしない。'
for s in p['sheets']:s['tiles']=[x for x in p['items'] if x['sheet']==s['sheet']]
for name,data in [('plan.json',p),('semantic-review.json',reviews),('generation-notes.json',generation_notes),('repair-prompts.json',{str(k):v for k,v in edits.items()})]:(O/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Recorded visual review for all 34 adopted sheets and 544 illustrations.')
