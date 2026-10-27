import json,csv,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;B=H/'2026-10-27-play1024'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
rows=read(B.with_suffix('.review.json'));plan=read(H/'manifest-additions.json')
advanced={'投扇興','コントラクトブリッジ','ブリッジ','ホイスト','スペード','ハーツ','ナポレオン','カナスタ','クリベッジ','ユーカー','ピノクル','カシノ','ジンラミー','ラミー','セブンカードスタッド','オマハポーカー','オマハ','テキサスホールデム','ホールデム','トリックテイキング','ワーカープレイスメント','エリアマジョリティ','ハンドマネジメント','セットコレクション'}
for x in rows:
 if x['category']=='仮面ライダー':x['meaning']=x['meaning'].replace('変身ヒーロー','戦士')
 if x['word']=='仮面ライダー':x['meaning']='変身して敵と戦う戦士たちを描く日本の特撮ヒーローシリーズ。';x['source']='https://www.kamen-rider-official.com/';x['lexicalSource']['url']=x['source']
 if x['word'] in advanced:
  x['grade']=4;x['ageReason']='詳しい遊び方や専門的なゲームの仕組みを表す語としてL4。'
for e in plan:
 if '『仮面ライダー』' in e['meaning']:e['meaning']=e['meaning'].replace('変身ヒーロー','戦士')
 if e['word']=='仮面ライダー':e['meaning']=next(x['meaning'] for x in rows if x['word']=='仮面ライダー')
 for a in e['aliases']:
  x=next(x for x in rows if x['id']==a['id']);a['meaning']=x['meaning']
save(H/'manifest-additions.json',plan);save(B.with_suffix('.review.json'),rows)
header='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
B.with_suffix('.csv').write_text(header+'\n'+'\n'.join(','.join(str(x[k]) for k in header.split(',')) for x in rows)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(dict(advanced=sum(x['grade']==4 for x in rows))))
