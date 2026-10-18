"""Record meaning-specific age decisions after reviewing the entire daily-word plan."""
import collections,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-18-expansion1024h'
p=json.loads((OUT/'plan.json').read_text(encoding='utf-8'))
# These are exact words in this frozen batch, each with exactly one reviewed meaning.
# Familiarity of the meaning, rather than the difficulty of its kanji, determines the band.
g2=set('''愛犬 アイシャドウ アウトレット アジア 預かり アフリカ アルプス アレルギー アワビ 案 暗雲 安眠 言い分 家出 行き過ぎ 生き残り 偉人 一方通行 移転 衣料品 印鑑 院長 イントロ ウイルス ウェイトレス ウェブページ 受取人 うねり 生まれつき 占い師 運搬 沿岸 沿線 円盤 王者 凹凸 大相撲 大関 大水 お金持ち 教え子 オフィス オペラ おもてなし 親孝行 音階 恩人 音声 音程 音読み オークション オーディオ オール 会員 海岸線 会社員 回数券 海面 カウボーイ 係員 カセット 家電 金持ち 花粉 花粉症 カルメラ 関西 関西弁 管制塔 寒中 神主 甲板 観覧 管理人 学園 楽隊 楽団 眼科医 元旦 ガードマン キオスク 刻み 汽船 貴重品 几帳面 キャスター キャンペーン 給油 キュロット 教員 共感 競走馬 共有 共用 曲目 巨体 キログラム キロメートル 金貨 金額 近眼 金屏風 儀式 銀貨 ギタリスト 魚介類 魚群 漁港 漁船 漁村 魚類 銀紙 区間 句読点 区役所 クルーザー クレンザー クレーター 訓読み グライダー グリップ グリル グランプリ 計測 消印 検診 建築士 ケープ 下旬 月刊 工員 高温 行楽地 コスプレ コットン 個展 諺 湖畔 コリー 懇談 コンドル コンバイン 強情 五感 碁盤 殺菌 珊瑚 財産 在宅 雑踏 雑音 雑談 試運転 シェパード シェルター シェーバー 市外 紫外線 式典 資源 四国 詩人 視線 下調べ 湿疹 市民 写真家 収録 守衛 宿舎 珠算 主審 主治医 絶滅 ゼラチン 善悪 創作 奏者 送信 操縦 双生児 創造力 装着 送別会 創立 即席 測定 側面 速力 卒業生 祖父母 ソーイングセット 雑木林 増減 対局 体型 タイミング 太陽電池 互い違い タキシード 炊き出し 託児所 卓上 タグボート 達筆 卵形 俵 タンカー タンクローリー 単行本 代打 代役 楕円 脱皮 団員 談笑 壇上 断水 団体 団地 断面 段落 弾力 チェロ 稚魚 父方 中古車 中旬 中途半端 中腹 厨房 朝刊 長寿 長短 頂点 長編 貯水池 陳列 通院 通勤 通帳 通訳 付き添い 梅雨明け 梅雨入り 定員 庭園 低温 訂正 テーマ 天文台 テーマソング バギー 爆音 抜群 バリカン バルコニー 番地 バント バンパー バージョン バーベル パステル パスポート パターン パッチワーク パノラマ パビリオン パフォーマンス パラグライダー パラリンピック パントマイム パーカッション パーツ パール 比較 干潟 引き継ぎ 引き伸ばし 被写体 筆跡 一人暮らし 一人旅 火鉢 皮膚科 表札 表彰 平仮名 美術展 ビュッフェ 秒速 屏風 便箋 ピラニア ピラミッド ピント ファンクラブ フィルター フィルム 風味 フェアプレー フェイント フェスティバル フェルト フォワード フォークソング フォーム 復元 複写 複数 服用 付着 不燃物 譜面 フラワーアレンジメント フリーハンド フリーパス フリーマーケット フレーム 噴火 噴射 粉末 部首 仏像 ブラスバンド ブリキ ブレザー ブレーカー ブログ 分割 分校 文書 文通 分量 プライバシー プラカード プラグ プラネタリウム'''.split())
g3=set('浮世絵 オーボエ カルメラ 寄生虫 湿原 ソプラノ ティンパニ バードコール パラボラアンテナ'.split())
for x in p['items']:
 grade=3 if x['word'] in g3 else 2 if x['word'] in g2 else 1
 x.update(grade=grade,level=grade,ageReason={1:'家庭・低学年の学校生活・遊び・物語などで一般に触れ、具体物や身近な場面で意味を説明できる語義。',2:'一般語だが語の呼び名や内容の理解には、中学年程度の学習・社会経験を見込む語義。低学年用CPUには混ぜない。',3:'伝統美術・専門的な道具や楽器・生物のしくみなどの知識を含み、高学年の学習や読書を見込む語義。'}[grade])
save=lambda f,o:f.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save(OUT/'plan.json',p)
save(OUT/'age-review.json',dict(criteria='一般児童が意味を理解できる範囲で語義ごとに判定。漢字を読めるかとは別。',gradeCounts=dict(collections.Counter(x['grade'] for x in p['items'])),items=[{k:x[k] for k in ('id','reading','word','meaning','grade','ageReason')} for x in p['items']]))
byrd={x['reading']:x for x in p['items']};s=json.loads((OUT/'sheets.json').read_text(encoding='utf-8'))
for sh in s:sh['tiles']=[byrd[x['reading']] for x in sh['tiles']]
save(OUT/'sheets.json',s)
print(json.dumps(dict(collections.Counter(x['grade'] for x in p['items'])),ensure_ascii=False))
