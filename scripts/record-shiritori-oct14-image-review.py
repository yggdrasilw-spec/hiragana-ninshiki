"""Save the sheet-by-sheet visual review and full generation provenance."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'data/image-coverage/2026-10-14-expansion512-images'
notes={
1:'くしゃみ・縮む・潜るなどの動作を確認。縮むは同じ服の大小、空くは席の使用前後。',
2:'歩む・荒れる・暗記・育児などの場面を確認。祝いのコマの罫線色混入は再編集後に機械検証。',
3:'浮くを水面で静かに浮く姿へ修正。唸るは口から低い声の線が出る姿へ修正。写すと映るを区別。',
4:'起こすは眠っている子を起こす場面。怒る・踊る・覆う・送る・介護・会話を説明と対応。',
5:'掛けるはフックへかばん、加速は車の速さの増加。仮装・枯れる・借りる等を確認。',
6:'看護・企画・着替え・競う・寄贈・帰宅・気づく等を確認。緩和は辛さをやわらげる一例。',
7:'崩す・砕く・配る・汲む・曇る・悔やむ・来る・暮れる等を確認。交互は順の入れかわり。',
8:'拒む・混む・込める・子守・籠もる・肥やす・雇用・孤立等を確認。',
9:'司会・叱る・茂る・思考・試作・指示・沈む等を確認。沈むは石が水中へ沈む図。',
10:'締まるはふたの締め付け。染みるは水がスポンジへ入る。鳴るは時計の振動。図示・抱く・研ぐ等を確認。',
11:'降る・減る・保護・補佐・保持・彫る・舞う・見る等を確認。予知は気象の予測場面の一例。',
12:'ささやか・消極的・的確・莫大・不正確などを確認。不正確は針の値と比較。抽象語は場面例。',
13:'イコールは左右3個ずつ。一律は同じ贈り物。大げさは実物の小魚と話中の大魚へ修正。',
14:'多めは盛りの比較。カチカチは砕けない石に修正。カラフル・華麗・軽やか・簡潔を確認。',
15:'簡素・完璧・寒冷・頑固・気がかり・気軽等を確認。均一の焼き菓子を含め場面例を照合。',
16:'均等は4等分のピザ。逆は反対の矢印。高度は空中の高さではなく精密なロボット組立へ修正。',
17:'小幅は同じ長さで幅の異なるリボン。互角は同じ勢いの対戦。自明は明らかに空の透明なコップの例。',
18:'正規・粗大・ソフト・素朴・粗末・平ら等を確認。独自は他と違う器の柄の一例。',
19:'値打ちの宝冠の罫線色混入を修正。フェア・不屈・不慣れ・不備・不明等の場面を確認。',
20:'稀は多数の灰色玉に青玉1個へ修正。無害は生きた野生のカエルから布のぬいぐるみへ修正。',
21:'おしべの花粉とめしべの先・子房を区別。みぞれは雨と雪の混在。レアの宝石色と不均等罫線を修正。',
22:'痣は皮膚の色の違い、厚さと厚みは面間の距離、足場・宛名・雨戸・安否・アンプなどを確認。',
23:'五つはリンゴ5個、五日は5番目の升。一度は紙飛行機を1回飛ばす例。鋳型と硫黄を確認。',
24:'鋳物・以来・入れ歯・インク・ウェブ等を確認。鋳型の道具と鋳物の結果を別の意味として対応。',
25:'枝葉・笑み・絵文字・獲物・エリア・エール等を確認。扇は折り畳める形、王座は席、王妃は人物。',
26:'重さと重しを区別。数はものの個数。過疎は人の少ない地域の例。黴・蚊帳・崖を確認。',
27:'柄・機器・木々・器具・季語・基礎・基地等を確認。再生成して等寸の罫線検証に合格。',
28:'四肢は左右の手足、軸は車輪の中心。時差は曖昧な時計絵から2本の針の正確な8時間差図へ差し替え。',
29:'〇は空の皿、ソロは1人の演奏、縦と谷を区別。ダム・地下・地区・弟子・刺・土器・土手を確認。',
30:'ミリは1cmを10等分した正確な模式図へ差し替え。無地は模様なし。矛・ノブ・皮膚・武士等を確認。',
31:'雌は母牛と子、ラメは金属のように光る織物。和語は風景だけでなく自然の語の絵を話す人物へ修正。',
32:'王手は駒の成りの絵を採用せず、飛車の縦の利きが王へ届く正確な模式図へ差し替え。コール・在庫等を確認。'
}
plan=json.loads((DIR/'plan.json').read_text(encoding='utf-8'))
semantic=[]
for n in range(1,33):
    items=[x for x in plan['items'] if x['sheet']==n]
    semantic.append(dict(sheet=n,passed=True,reviewedAt='2026-10-14',notes=notes[n],
        limitation='抽象語は具体的な場面例。画像だけで語義全体を示すという判定ではない。',
        items=[{k:x[k] for k in ['id','reading','word','meaning','filename','sourceSheet']} for x in items]))
    for x in items:
        if x.get('credit')=='プログラム生成図':continue
        suffix='\nPalette instruction: use natural blue, green, orange, brown and golden yellow. Avoid fuchsia, purple and magenta pigments in artwork; magenta belongs ONLY to the preserved grid.' if n>=10 else ''
        original=(DIR/f'sheet{n:02}-prompt.txt').read_text(encoding='utf-8')+suffix
        x['prompt']=original+'\nContent review: '+notes[n]+'\nFull generation and correction requests: data/image-coverage/2026-10-14-expansion512-images/imagegen-orchestration.json'
        (ROOT/'assets/shiritori'/x['sourceSheet']).with_suffix('.prompt.txt').write_text(x['prompt'],encoding='utf-8')
(DIR/'semantic-review.json').write_text(json.dumps(semantic,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(DIR/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
source=Path('C:/Users/user/.codex/sessions/2026/10/13/rollout-2026-10-13T21-13-47-01a1352e-e0f4-75f0-8679-617dbe48a372.jsonl')
calls=[]
for line in source.open(encoding='utf-8'):
    x=json.loads(line);p=x.get('payload',{})
    if x.get('type')!='response_item' or p.get('type') not in ('function_call','custom_tool_call'):continue
    code=p.get('arguments',p.get('input',''))
    if code.lstrip().startswith('// @exec:') and 'await tools.image_gen__imagegen(' in code:
        calls.append(dict(timestamp=x.get('timestamp'),code=code))
(DIR/'imagegen-orchestration.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
template=ROOT/'assets/shiritori/sheets/equal-grid-4x4-oct14.png'
if not template.exists():shutil.copyfile('C:/Users/user/.codex/skills/shiritori-image-sheets/assets/equal-grid-4x4.png',template)
rejected=[{'sheet':2,'version':1,'reason':'Tile16 divider color leaked'}, {'sheet':19,'version':1,'reason':'Tile2 divider color leaked'},
 {'sheet':21,'version':1,'reason':'Grid line3 displaced'},{'sheet':21,'version':2,'reason':'Grid line3 displaced'},
 {'sheet':21,'version':3,'reason':'Tile6 divider color leaked'},{'sheet':23,'version':1,'reason':'Cell dimensions inconsistent'},
 {'sheet':23,'version':2,'reason':'Cell dimensions inconsistent'},{'sheet':24,'version':1,'reason':'Divider fringe unstable'},
 {'sheet':24,'version':2,'reason':'Tile6 divider color leaked'},{'sheet':27,'version':1,'reason':'Cell dimensions inconsistent'}]
(DIR/'rejected-sheets.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'reviewedWords':512,'sheets':32,'generationOrchestrationCalls':len(calls),'programDiagrams':3}))
