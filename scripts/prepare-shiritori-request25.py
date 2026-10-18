"""Plan the requested vocabulary and nearby meanings against the current dictionary."""
import csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/image-coverage/2026-10-19-request25'
OUT.mkdir(parents=True,exist_ok=True)
requested='めんこ うしがえる めっき すもも ねばり とんねる うんざり りもーと うむらうと こんすたんてぃのーぷる でみぐらすそーす くみたいそう きみがよ びら るっくす るろう くびながりゅう みんく くろうと しぼう らぐ ぷーま ぐりこ ししまい こまいぬ'.split()
nearby='べーごま びーだま おはじき たけとんぼ けんだま あまがえる とのさまがえる ひきがえる かじかがえる もりあおがえる めたる きんめっき ぎんめっき とたん ぶりき あんず あんずじゃむ ぷるーん ねばりけ ねんせい ねばりづよさ ずいどう ちかどう りもーとわーく てれわーく えんかく おんらいんかいぎ だいあくりてぃかるまーく びざんつ びざんてぃうむ いすたんぶーる ほわいとそーす べしゃめるそーす ぶらうんそーす くみたてたいそう こっか さざれいし ちらし りゅうろう そぞろあるき ぷれしおさうるす えるもさうるす かわうそ てん いたち しろうと たくみ じゅくれん しぼうぶん ないぞうしぼう たいぼう しぼうこう しぼうこうちょう じゅうたん らぐまっと たいむらぐ ぴゅーま くーがー えざきぐりこ ぐりこーげん ししがしら かぐら いしかり うんぎょう あぎょう さんどう'.split()
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
for r in requested+nearby:
 matches=[(i+1,x['word'],x['meaning']) for i,x in enumerate(rows) if x['reading']==r]
 print(r,json.dumps(matches,ensure_ascii=False))
data=json.loads(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
print('JMdict keys',list(data)[:8])
entries=[x for x in data['words'] if any(k['text'] in requested+nearby for k in x.get('kana',[]))]
(OUT/'lexical-candidates.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('matching dictionary entries',len(entries))
