"""Attach frozen dictionary evidence and honest browser/source retrieval metadata."""
import json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-16-expansion1024f'
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));audit=json.loads((OUT/'source-audit.json').read_text(encoding='utf-8'))
dictionary=json.loads(Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json').read_text(encoding='utf-8'))
def norm(s):return unicodedata.normalize('NFKC',s).translate(str.maketrans({chr(i):chr(i-96) for i in range(0x30a1,0x30f7)})).replace('・','')
index={}
for e in dictionary['words']:
 for f in e['kanji']+e['kana']:index.setdefault(norm(f['text']),[]).append(e)
maker_urls={'ロッテ':'https://www.lotte.co.jp/products/','湖池屋':'https://www.koikeya.co.jp/','三幸製菓':'https://www.sanko-seika.co.jp/','栗山米菓':'https://www.befco.jp/','三立製菓':'https://www.sanritsuseika.co.jp/products/','アトリオン製菓':'https://www.atrion-s.com/products/page/1','オリオン':'https://www.orionstar.co.jp/','東ハト':'https://www.tohato.jp/products/','ヤマザキビスケット':'https://www.yamazaki-biscuits.co.jp/products/','クラシエ':'https://www.kracie.co.jp/foods/okashi/','有楽製菓':'https://www.yurakuseika.co.jp/lineup/','よっちゃん食品工業':'https://www.yotchan.co.jp/','共親製菓':'https://www.kyoushin-s.co.jp/','丸川製菓':'https://marukawaseika.co.jp/','コリス':'https://www.coris.co.jp/','カクダイ製菓':'https://www.kuppyramune.co.jp/','宮田製菓':'https://www.miyataseika.co.jp/','中野物産':'https://www.nakanobussan.co.jp/','松岡製菓':'https://www.mangetupon.co.jp/','マスヤ':'https://www.masuya.co.jp/','パインの':'https://www.pine.co.jp/'}
records=[]
for x in plan['items']:
 refs=list(x['sources'])
 for maker,url in maker_urls.items():
  if maker in x['meaning']:refs.insert(0,url);break
 if x['category']=='日産の車種':refs.append('https://www.nissan.co.jp/HERITAGE/')
 matches=[e for e in index.get(norm(x['word']),[]) if any(norm(k['text'])==x['reading'] for k in e['kana'])]
 row=dict(slot=x['slot'],word=x['word'],reading=x['reading'],category=x['category'],authoredDefinition=x['meaning'],sources=list(dict.fromkeys(refs)),reviewMethod='語義は独自編集。辞書の同一表記・読み照合は名称の補助証拠であり、同音の別対象や説明全体の自動実証とは扱わない。')
 if matches:row['dictionaryEvidence']=dict(database='JMdict',date=dictionary['dictDate'],entries=[dict(id=e['id'],kana=[k['text'] for k in e['kana']],kanji=[k['text'] for k in e['kanji']]) for e in matches])
 records.append(row)
audit['rows']=records
audit['browserCheckedPages']=[dict(url=u,checkedDate='2026-10-16',method='組み込みブラウズで本文・見出しを確認。全商品の個別照合を意味しない。') for u in ['https://www.nao.ac.jp/new-info/planet.html','https://www.nao.ac.jp/new-info/satellite.html','https://www.iau.org/public/themes/naming_stars/','https://la28.org/en/games-plan/olympics.html','https://support.olympics.com/hc/en-gb/articles/43002667811219-What-sports-are-in-the-Olympic-Winter-Games-Milano-Cortina-2026','https://www.joc.or.jp/sports/pentathlon/index.html','https://www.atrion-s.com/products/page/1','https://www.suntory.co.jp/softdrink/','https://www.lotte.co.jp/products/','https://www.calbee.co.jp/products/','https://www.mazda.co.jp/cars/','https://www.honda.co.jp/auto-archive/','https://www.nissan.co.jp/HERITAGE/','https://www.subaru.jp/carlineup/','https://www.bourbon.co.jp/product/','https://sekiei.nichibun.ac.jp/YoukaiDB/search.html','https://www.theoi.com/greek-mythology/bestiary.html']]
audit['retrievalNote']='端末からのurllib取得はDNS制限で失敗。上記のbrowserCheckedPagesは組み込みブラウズで別途確認。外部の画像・説明文は取り込まず独自に作成。未閲覧の個別製品ページまで確認済みとはしていない。'
(OUT/'source-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(entries=len(records),dictionaryMatches=sum('dictionaryEvidence' in x for x in records),browserPages=len(audit['browserCheckedPages'])),ensure_ascii=False))
