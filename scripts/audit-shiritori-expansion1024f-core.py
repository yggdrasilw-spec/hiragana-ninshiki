"""Check requested core coverage against meanings, including existing entries."""
import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-16-expansion1024f'
items=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))['items']
old=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
expected={
'八惑星':'水星 金星 地球 火星 木星 土星 天王星 海王星',
'五準惑星':'ケレス 冥王星 エリス ハウメア マケマケ',
'代表的な衛星':'月 フォボス ダイモス イオ エウロパ ガニメデ カリスト タイタン エンケラドス ミマス テティス ディオネ レア イアペトゥス ヒペリオン ミランダ アリエル ウンブリエル チタニア オベロン トリトン カロン',
'代表的な恒星':'太陽 シリウス カノープス アークトゥルス ベガ カペラ リゲル プロキオン ベテルギウス アルタイル アルデバラン アンタレス スピカ ポルックス フォーマルハウト デネブ レグルス カストル ポラリス',
'LA28競技分野':'スリーエックススリー アーチェリー 体操競技 アーティスティックスイミング 陸上競技 バドミントン 野球 バスケットボール ビーチバレー ビーエムエックスフリースタイル ビーエムエックスレーシング ボクシング スポーツクライミング クリケット ロードレース トラックレース 飛び込み 馬術 フェンシング フラッグフットボール サッカー ゴルフ ハンドボール ホッケー 柔道 ラクロス 近代五種 マウンテンバイク競技 オープンウォータースイミング 新体操 ローイング コースタルローイング 七人制ラグビー セーリング 射撃 スケートボード競技 カヌースラローム ソフトボール カヌースプリント スカッシュ サーフィン 競泳 卓球 テコンドー テニス トランポリン競技 トライアスロン バレーボール 水球 ウエイトリフティング レスリング',
'冬季16分野':'アルペンスキー バイアスロン ボブスレー クロスカントリースキー カーリング フィギュアスケート フリースタイルスキー アイスホッケー リュージュ ノルディック複合 ショートトラック スケルトン スキージャンプ スキーマウンテニアリング スノーボード スピードスケート',
'指定飲料と車':'コーラ コカ・コーラ ペプシ ファンタ CCレモン アクエリアス ポカリスエット NSX',
}
report=[]
for group,words in expected.items():
 for word in words.split():
  matches=[dict(source='今回',word=x['word'],reading=x['reading'],meaning=x['meaning'],category=x['category']) for x in items if x['word']==word]
  matches += [dict(source='既存',word=x['word'],reading=x['reading'],meaning=x['meaning']) for x in old if x['word']==word]
  # Reject names used only as cars, brands, or fiction when checking astronomy/sports.
  if group in ['八惑星','五準惑星','代表的な衛星','代表的な恒星']:
   matches=[x for x in matches if any(t in x['meaning'] for t in ['惑星','衛星','恒星','巨星','地球の周','ふたご座'])]
  if group in ['LA28競技分野','冬季16分野']:
   matches=[x for x in matches if x.get('category') in ['スポーツ','冬のスポーツ'] or any(t in x['meaning'] for t in ['競技','スポーツ','すぽーつ','球技','武道','泳ぎ','ダンス'])]
  report.append(dict(group=group,word=word,present=bool(matches),matches=matches))
missing=[x for x in report if not x['present']]
(OUT/'core-coverage.json').write_text(json.dumps(dict(scope='LA28公式分野と2026冬季16分野を基準に照合。全メダル種目の男女別距離別の網羅とは区別する。',sources=['https://la28.org/en/games-plan/olympics.html','https://support.olympics.com/hc/en-gb/articles/43002667811219-What-sports-are-in-the-Olympic-Winter-Games-Milano-Cortina-2026','https://www.nao.ac.jp/new-info/planet.html','https://www.nao.ac.jp/new-info/satellite.html'],checks=report,missing=missing),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(checked=len(report),missing=[x['word'] for x in missing]),ensure_ascii=False));assert not missing
