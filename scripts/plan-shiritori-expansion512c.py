import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'data/image-coverage/2026-10-15-expansion512c'
p=json.loads((OUT/'draft.json').read_text(encoding='utf-8'))
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
aliases={'スマートフォン':'スマホ','パソコン':'パソコン','グミ':'グミ','綿飴':'綿飴','ジーンズ':'ジーンズ','ぬいぐるみ':'ぬいぐるみ','シャープペンシル':'シャープペンシル','ペンケース':'筆箱','バックパック':'リュックサック','レインブーツ':'長靴'}
groups={}
full_groups={'ぱーそなるこんぴゅーたー':'パソコン','ゆにばーさるしりあるばす':'USB','こんぱくとでぃすく':'CD','ばっくぐらうんどみゅーじっく':'BGM','ますたーおぶせれもにー':'司会','みゅーじっくびでお':'MV','のーぐっど':'NG','もすとばりゅあぶるぷれいやー':'MVP','こんびにえんすすとあ':'コンビニ','ふぁみりーれすとらん':'ファミレス','だいらんとうすまっしゅぶらざーず':'brand:SmashBros','らすとぼす':'ラスボス','こぴーあんどぺーすと':'コピペ','えきべんとう':'駅弁','でこれーしょん':'デコ','ぷりんとくらぶ':'プリクラ'}
for x in p['items']:
 x['group']=full_groups.get(x['reading'],x['group'])
 groups.setdefault(x['group'],[]).append(x)
matches=[]
for group,items in groups.items():
 found=[dict(id=i,**r) for i,r in enumerate(rows,1) if r['image_asset'] and r['word']==aliases.get(group,group)]
 if found:matches.append(dict(group=group,targets=[x['id'] for x in items],candidates=found))
(OUT/'reuse-candidates.json').write_text(json.dumps(matches,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(groups=len(groups),brands=sum(g.startswith('brand:') for g in groups),reuse=matches),ensure_ascii=False))
diagram_groups=set('字 図 AI USB QRコード CD BGM MV NG OK HP MP ダブルタップ スワイプ スクロール ピンチイン ピンチアウト ドラッグ ドラッグアンドドロップ ダブルクリック 右クリック コピー ペースト コピペ 切り取り スクリーンショット 画面録画 一時停止 ミュート 音量 画面 ホーム画面 ロック画面 アプリアイコン アイコン 壁紙 ウィジェット ダークモード マナーモード 機内モード パスワード パスコード インストール アンインストール ダウンロード アップロード アップデート ブラウザー ホームページ ウェブサイト ブックマーク 検索窓 検索キーワード フォルダ ビデオ通話 チャット ボイスチャット メッセージ スタンプ 顔文字 音声入力 手書き入力 ローマ字入力 フリック入力 かな入力 通知 電子メール メールアドレス プログラミング ブロックプログラミング ロボットプログラミング 3Dモデル ドット ドット絵 ピクトグラム ペイント 生成AI 音声アシスタント 翻訳アプリ 読み上げ オンライン学習 デジタル教科書 デジタルドリル 学習アプリ クイズアプリ お絵描きアプリ スライド スライドショー タイピング エンターキー スペースキー ホームポジション セーブ セーブデータ ロード リトライ コンティニュー ゲームオーバー クリア レベル ランク スコア ハイスコア ベストスコア チェックポイント パワーアップ レベルアップ ランクアップ チュートリアル 自動保存 課金 無課金 エモート アバター スキン キャラメイク シールド クエスト ミッション アイテム スーパーレア ボス ラスボス 中ボス 敵 キャラクター ステージ 攻略 フレンド フレンドコード リズムゲーム パズルゲーム 対戦ゲーム アクションゲーム レースゲーム RPG サムネイル チャンネル登録 ループ再生 倍速再生 字幕 ハッシュタグ 2D 3D'.split())
reuse={x['group']:x['candidates'][0] for x in matches}
new=[];diagrams=[]
for group,items in groups.items():
 base=items[0];filename=f'expansion512c-word-{base["id"]}.png'
 assignment='reused' if group in reuse else 'diagram' if group in diagram_groups or group.startswith('brand:') else 'new'
 if assignment=='reused':filename=reuse[group]['image_asset'].split('/')[-1]
 for x in items:x.update(filename=filename,assignment=assignment if x is base else ('reused' if assignment=='reused' else 'shared-new'),sourceId=reuse[group]['id'] if assignment=='reused' else base['id'],credit='プログラム生成図' if assignment=='diagram' else 'AI生成イラスト',reuseReason='同じ対象・語義「'+group+'」を示す画像。別名・略称は対象を変えず共有。')
 if assignment=='new':new.append(dict(base,sharedIds=[x['id'] for x in items]))
 elif assignment=='diagram':diagrams.append(dict(base,sharedIds=[x['id'] for x in items]))
for i,x in enumerate(new):
 x.update(sheet=i//16+1,tileIndex=i%16+1,sourceSheet=f'sheets/expansion512c-sheet{i//16+1:02}.png',cropValidation=f'data/image-coverage/2026-10-15-expansion512c/sheet{i//16+1:02}-crop.json')
for n in range(1,(len(new)+15)//16+1):
 tile=[x for x in new if x['sheet']==n]
 prompt='Edit the attached 2048x2048 equal 4x4 template. Keep all five vertical and all five horizontal pure MAGENTA #ff00ff lines including outer frame, identical equal cell geometry and line thickness. Draw 16 independent clear warm picture-book watercolor illustrations, one per cell, row-major order. Each artwork stays inside its cell. Magenta is reserved for the grid; use blue, green, orange, brown, neutral colors for art. No text, letters, labels, numbers, watermarks or logos. No arbitrary white-margin requirement; use each cell generously. Accurate recognizable objects and actions, distinct shapes for similar subjects.\n'
 for j in range(16):
  prompt+=str(j+1)+'. '+(tile[j]['word']+' — '+tile[j]['meaning'] if j<len(tile) else 'A smooth grey pebble. Filler only.')+'\n'
 for x in tile:x['prompt']=prompt;x['scene']=x['word']+'：'+x['meaning']
 (OUT/f'sheet{n:02}.prompt.txt').write_text(prompt,encoding='utf-8')
p.update(newImages=new,diagrams=diagrams,sheets=(len(new)+15)//16,reuseReviews=matches)
(OUT/'plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(words=len(p['items']),newIllustrations=len(new),diagrams=len(diagrams),sheets=p['sheets'],reusedGroups=len(matches)),ensure_ascii=False))
