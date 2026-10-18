"""Build a portable Colab notebook embedding the tested synthesis module."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
cells = []


def cell(kind, source):
    item = {"cell_type": kind, "metadata": {}, "source": source.strip().splitlines(keepends=True)}
    if kind == "code":
        item.update(execution_count=None, outputs=[])
    cells.append(item)


cell("markdown", """
# カタカナ72文字：濁点・半濁点の自動合成と学習

元の `etl5_train_resume.ipynb` をもとにした別実験です。
清音46文字の順番を維持し、濁音20文字・半濁音5文字・ヴを追加します。
**元データ・元モデルは上書きしません。上から順に実行してください。**

1. ColabのGPUランタイムを選び、画像ZIPを左のファイル欄からアップロード
2. 準備・設定・ZIP展開・データ監査を実行
3. 自動合成プレビューで点の位置や大きさを確認
4. 原画像単位で分割して学習（筆記者CSVは任意）
5. 独立したテスト分割で評価。実際の手書きでも別途確認
6. 必要ならTensorFlow.jsへ変換

既存の `processed_dataset/ｶ/*.png` のような半角フォルダ、全角フォルダの両方に対応。
手書き画像そのものは、このノートブックに同梱していません。
合成器はフォントを使わず、揺らぎのある２本の線／輪を自動描画します。
手書きの点を用意できる場合は、後述のMARK_BANKに差し替えられます。

配置v2：実際の墨線間の距離を基準に、80%を近め・20%を離れた配置にします。
接触しない範囲で位置をランダム化します。旧実験と出力・キャッシュを分離します。
""")
cell("code", """
# 1. Colabに入っているTensorFlowを優先して使います。
# 存在しない場合だけ対応する版を取得。失敗したらこのセルで停止します。
import importlib.util, subprocess, sys
print('Python:', sys.version)
if importlib.util.find_spec('tensorflow') is None:
    subprocess.run([sys.executable, '-m', 'pip', 'install',
                    'tensorflow>=2.20,<2.23'], check=True)
missing = [package for module, package in [('PIL', 'pillow'), ('matplotlib', 'matplotlib')]
           if importlib.util.find_spec(module) is None]
if missing:
    subprocess.run([sys.executable, '-m', 'pip', 'install', *missing], check=True)
import tensorflow as tf
print('TensorFlow:', tf.__version__)
print('GPU:', tf.config.list_physical_devices('GPU'))
from google.colab import drive
drive.mount('/content/drive')
""")
module = (HERE / "katakana_training.py").read_text(encoding="utf-8")
cell("code", "# 2. 合成・学習モジュール（このセルに全コードを同梱）\n" + module)
cell("code", """
# 3. 設定：元モデルとは別の出力先です。
# DriveのダウンロードでZIPが複数になった場合も、全部そのままアップロード。
ZIP_PATHS = [p for p in sorted(Path('/content').glob('*.zip')) if not p.name.startswith('real-')]
# 実筆テスト用のreal-*.zipは学習用データに混ぜません。
# 無関係なZIPがある場合: ZIP_PATHS = ['/content/part1.zip', '/content/part2.zip', ...]
LOCAL_DATASET_DIR = '/content/katakana-zip-local'
OUTPUT_DIR = '/content/drive/MyDrive/ETL/model_katakana_marks_v2_close_spacing'
BASELINE_MODEL = '/content/drive/MyDrive/ETL/model_katakana/model.h5'
# 元モデルがない場合だけ None に変更（最初から学習）。

GROUPS_CSV = None  # 例: '/content/drive/MyDrive/ETL/groups.csv'
# ユーザー確認: 元からある画像を使うため、原画像ごとの分割を標準にします。
# 別途増幅した画像を混ぜる場合は、GROUPS_CSVに元画像のIDを設定してください。
CONFIRM_ONE_PNG_PER_ORIGINAL = True
MARK_BANK = None   # 手書き点のフォルダ。Noneなら自動描画。
POLARITY = 'auto'  # auto / white_on_black / black_on_white
VARIANTS = 2       # 各原画像・各文字の合成バリエーション数
EPOCHS = 100
BATCH_SIZE = 128
SEED = 20261016
# 原画像の由来が不明なまま、合成動作を試す実験に限りTrue。
# その成績を独立した認識率として扱わないでください。
ALLOW_UNVERIFIED_GROUPS = False

if BASELINE_MODEL and not Path(BASELINE_MODEL).is_file():
    raise FileNotFoundError(f'元モデルが見つかりません: {BASELINE_MODEL}')
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
print('72文字:', ''.join(LABELS))
""")
cell("code", """
# 3.5. アップロード済みZIPをColab内で展開。DriveのPNGは読みません。
# Colab左のフォルダアイコン → ファイルをアップロード → 分割されたZIPをすべて選択。
# 『processed_dataset/ｶ/*.png』でも『ｶ/*.png』でも自動で認識します。
# ZIPの中身は、元データまたは前処理済みの文字別PNGフォルダにしてください。
# 再実行では同じZIPの展開済みファイルを再利用します。
print('使用するZIP:', [str(path) for path in ZIP_PATHS])
DATASET_DIR = extract_dataset_zip(ZIP_PATHS, LOCAL_DATASET_DIR)
print('以後の画像読込先:', DATASET_DIR)
""")
cell("markdown", """
### 学習用と評価用の混入を防ぐ設定

元ノートは各文字2,800枚を使っていますが、これらが元画像を増幅したものなら、
単純にファイルを分けても同じ原画像の派生が両方に入り、成績が高く出ます。

`groups.csv` の例（pathはDATASET_DIRからの相対パス）:

```csv
path,group
ｶ/original0001.png,writer001
ｶ/original0001_rotate.png,writer001
ｷ/original0002.png,writer001
ｶ/original0003.png,writer002
```

**標準では筆記者CSVなしで、そのまま学習できます。**
元からある画像を使うという確認に基づき、`CONFIRM_ONE_PNG_PER_ORIGINAL = True` にしています。
原画像を先に学習・検証・テストへ分け、それから濁点・半濁点を合成します。
同じ原画像からできた清音・濁音・半濁音が、別の分割へ混ざることはありません。
完全一致の重複画像も除外します。

筆記者IDは、未知の筆記者に対する性能を別途測りたい場合の任意設定です。
その場合はCSVのgroupに筆記者IDを指定します。
すでに回転・拡縮などで増幅した画像を入力する場合も、CSVで同じ原画像の派生をまとめてください。
添付の `etl5_preprocess.ipynb` 自体は、切り抜き・拡縮だけで枚数を増やしていません。

任意の手書き点は `MARK_BANK/dakuten/train/*.png`、`dakuten/val/*.png`、
`dakuten/test/*.png`（handakutenも同様）に配置します。
点も原画像・筆記者を分け、別の分割へ同じ点をコピーしないでください。
""")
cell("code", """
# 4. データ監査 → 原画像グループの分割 → 合成対象リスト
from collections import Counter
import tensorflow as tf
tf.keras.utils.set_random_seed(SEED)
sources, audit = inventory(DATASET_DIR, GROUPS_CSV, SEED, POLARITY, CONFIRM_ONE_PNG_PER_ORIGINAL,
                           progress=True)
print('画像監査完了。合成対象リストを作っています…', flush=True)
examples = make_examples(sources, VARIANTS, SEED)
print(audit)
print('元画像:', Counter(r['split'] for r in sources))
print('合成後:', Counter(r['split'] for r in examples))
save_json(Path(OUTPUT_DIR) / 'source-audit.json', audit)
""")
cell("code", """
# 5. 合成プレビュー：上段=清音、中段=濁音、下段=半濁音
from IPython.display import display
sheet = preview(examples, DATASET_DIR, Path(OUTPUT_DIR) / 'preview.png', POLARITY, MARK_BANK)
display(sheet)
print('列:', ' '.join(VOICED))
print('濁音:', ' '.join(VOICED.values()))
print('点の近さ・接触・欠落を確認してください。近い配置と離れた配置を混ぜています。preview.jsonに文字と元画像を保存します。')
""")
cell("code", """
# 6. 学習：同じ設定・データなら、完了した最後のエポックから再開します。
# 初回は合成画像をローカルディスクにキャッシュします（規模により数GB）。
# ２エポック目以降は画像の再読込・再合成を省きます。
# 特徴抽出層と元の46出力を引き継ぎ、全層を再学習します。
# 過去のモデルのラベル順がBASE_LABELSと一致することが前提です。
best_model = train(examples, DATASET_DIR, OUTPUT_DIR, audit,
                   epochs=EPOCHS, batch=BATCH_SIZE, baseline=BASELINE_MODEL,
                   polarity=POLARITY, mark_bank=MARK_BANK,
                   allow_unverified_groups=ALLOW_UNVERIFIED_GROUPS)
""")
cell("code", """
# 7. テストはモデル選択に使っていない分割。
# 濁音のテスト画像も合成なので、実際の子どもの筆跡での精度とは別です。
baseline = tf.keras.models.load_model(BASELINE_MODEL, compile=False) if BASELINE_MODEL else None
result = evaluate(best_model, examples, DATASET_DIR, Path(OUTPUT_DIR) / 'test-report.json',
                  POLARITY, MARK_BANK, baseline)
print('合成テスト Top1 / Top5:', result['top1'], result['top5'])
print('清音・同じ入力で比較:', result.get('clean_same_inputs'))
for char, stats in result['characters'].items():
    print(char, stats)
""")
cell("markdown", """
### 実筆で確認してからアプリへ反映

`ガ`を実際に書いた画像と、清音に点を合成した画像は違います。
今回のテスト結果だけでは、実筆での認識率向上は判断できません。
指・ペン・マウスの実筆、点の位置が離れた文字、シ／ツ／ソ／ン、清音への誤った濁点付与を確認してください。

下の任意セルで、黒背景白文字／白背景黒文字の実筆PNGを
`REAL_DIR/ガ/*.png` のようにまとめて評価できます。
各画像は１文字。人が確認した正解フォルダに入れてください。
このデータを後から追加学習に使う場合、別の実筆テストを確保してください。
""")
cell("code", """
# 8. 合成ではない実筆の評価。収集アプリのZIPをアップロードして実行。
REAL_ZIP = None  # Noneなら/contentのreal-katakana-*.zipを自動検出。複数ある場合は1つのパスを指定。
REAL_DIR = None  # '/content/drive/MyDrive/ETL/real_katakana_test'
print('実筆評価を開始します。入力データを確認しています。', flush=True)
if not REAL_DIR or REAL_ZIP:
    REAL_ZIP = resolve_real_zip(REAL_ZIP)
if REAL_ZIP:
    print('使用する実筆ZIP:', REAL_ZIP, flush=True)
    REAL_DIR = extract_dataset_zip(REAL_ZIP, '/content/katakana-real-test', reserve_bytes=0,
                                   labels=LABELS, require_all=False)
if REAL_DIR:
    real = []
    for folder in sorted(Path(REAL_DIR).iterdir()):
        if folder.is_dir() and folder.name in LABELS:
            for path in sorted(folder.glob('*.png')):
                real.append((folder.name, path))
    if not real:
        raise ValueError('実筆画像がありません')
    print(f'実筆画像 {len(real)}枚・{len(set(char for char, _ in real))}文字を評価します。', flush=True)
    if 'best_model' not in globals():
        raise RuntimeError('評価モデルが未読込です。先に⑥の学習セルを実行してbest_modelを準備してください。')
    stats = {char: {'count': 0, 'top1': 0, 'top5': 0} for char in LABELS}
    for char, path in real:
        arr = np.asarray(normalize(ink_image(path)), dtype=np.float32)[None, ..., None] / 255.
        probs = best_model(arr, training=False).numpy()[0]
        ids = np.argsort(probs)
        entry = stats[char]
        entry['count'] += 1
        entry['top1'] += int(LABELS[ids[-1]] == char)
        entry['top5'] += int(LABELS.index(char) in ids[-5:])
    report = {'evaluation': 'real handwriting', 'characters': stats,
              'missing_characters': [c for c, s in stats.items() if not s['count']]}
    save_json(Path(OUTPUT_DIR) / 'real-test-report.json', report)
    total = len(real)
    top1 = sum(s['top1'] for s in stats.values()) / total
    top5 = sum(s['top5'] for s in stats.values()) / total
    print(f'実筆評価完了: {total}枚 / Top1 {top1:.1%} / Top5 {top5:.1%}')
    for char, entry in stats.items():
        if entry['count']:
            print(char, entry)
    print('未評価の文字:', ''.join(report['missing_characters']))
    print('結果保存先:', Path(OUTPUT_DIR) / 'real-test-report.json')
""")
cell("markdown", """
### TensorFlow.jsへの変換（任意、学習完了後）

現アプリのカタカナと同じGraphModel形式です。
コンバータは別のPython環境にインストールし、学習中のTensorFlowを変更しません。
変換用はPython 3.12を使い、Colab本体のPython版から切り離します。
依存関係の取得には時間と空き容量が必要です。
元の46文字モデルの出力先は変更しません。

変換結果を使う際は `model.json` と重みファイルに加え、
**`labels.json` の72文字順をアプリ側に反映する必要があります。**
このノートブックはアプリや公開モデルを自動で置き換えません。
""")
cell("code", """
# 9. SavedModelを別フォルダへ保存。既存の出力は削除しません。
import datetime
stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
saved = Path(OUTPUT_DIR) / ('saved_model-' + stamp)
best_model.export(str(saved))
""")
cell("code", """
# 10. 独立した変換環境を用意（初回のみインストール）。失敗は例外で停止。
import subprocess, sys

def run_conversion_command(command, log_name, env=None):
    # 子プロセスの本当のエラーを、CalledProcessErrorに埋もれさせない。
    log_path = Path(OUTPUT_DIR) / log_name
    print('実行:', ' '.join(map(str, command)), flush=True)
    with log_path.open('w', encoding='utf-8') as log:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, encoding='utf-8', errors='replace', env=env) as process:
            for line in process.stdout:
                print(line, end='', flush=True)
                log.write(line)
            code = process.wait()
    print('ログ保存先:', log_path, flush=True)
    if code:
        raise RuntimeError(f'変換の準備または実行が終了コード{code}で失敗しました。直前のログ末尾20〜40行を確認してください。全ログ: {log_path}')

converter_env = Path('/content/katakana-tfjs-env')
if not (converter_env / 'bin/python').exists():
    # 2.19のコンバータ環境をPython 3.13以降に作らないよう、3.12を明示。
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'uv'], check=True)
    subprocess.run([sys.executable, '-m', 'uv', 'venv', '--python', '3.12',
                    '--seed', str(converter_env)], check=True)
converter_python = str(converter_env / 'bin/python')
subprocess.run([converter_python, '-c',
                'import sys; assert sys.version_info[:2] == (3, 12), "変換用環境を新しいパスで作り直してください"'], check=True)
# TF 2.19はProtobuf<6。新しいYDFの生成済みprotoが6系を要求するため、
# TF-DFだけでなくYDFも対応版に固定する（Protobufだけ6へ上げない）。
converter_requirements = [
    'tensorflowjs==4.22.0', 'tensorflow==2.19.0', 'tf-keras==2.19.0',
    'tensorflow-decision-forests==1.12.0', 'ydf==0.11.0', 'protobuf==5.29.6',
    'setuptools==80.9.0',  # TensorFlow Hubが使うpkg_resourcesを含む版
]
run_conversion_command([converter_python, '-m', 'pip', 'install',
                        *converter_requirements], 'converter-install.log')
run_conversion_command([converter_python, '-m', 'pip', 'check'], 'converter-dependencies.log')
run_conversion_command([converter_python, '-c',
    'import sys, importlib.metadata as m; print(sys.version); '
    'print({p: m.version(p) for p in ["tensorflowjs", "tensorflow", "tf-keras", "keras", "numpy", "tensorflow-decision-forests", "ydf", "protobuf", "setuptools"]}); '
    'from pkg_resources import parse_version; '
    'from yggdrasil_decision_forests.dataset import data_spec_pb2; '
    'import tensorflowjs; '
    'print("pkg_resources / YDF Protobuf / TensorFlow.js import OK")'],
    'converter-versions.log')
tfjs_out = Path(OUTPUT_DIR) / ('tfjs-' + stamp)
run_conversion_command([str(converter_env / 'bin/tensorflowjs_converter'),
                '--input_format=tf_saved_model', '--output_format=tfjs_graph_model',
                str(saved), str(tfjs_out)], 'converter-' + stamp + '.log')
converted = json.loads((tfjs_out / 'model.json').read_text())
assert converted['format'] == 'graph-model'
for group in converted['weightsManifest']:
    for filename in group['paths']:
        assert (tfjs_out / filename).is_file(), filename
save_json(tfjs_out / 'labels.json', LABELS)
save_json(tfjs_out / 'preprocessing.json', {
    'size': 64, 'channels': 1, 'range': [0, 1], 'ink': 'white',
    'background': 'black', 'bbox_fit': .85, 'classes': len(LABELS),
    'note': 'Browser interpolation and Pillow interpolation are not pixel-identical.'})
print('変換完了:', tfjs_out)
print('ラベルも同時に更新してください:', ''.join(LABELS))
""")

notebook = {"nbformat": 4, "nbformat_minor": 5,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}, "colab": {"provenance": []}, "accelerator": "GPU"},
            "cells": cells}
for i, item in enumerate(cells):
    item["id"] = f"katakana-{i:02d}"
output = HERE / "etl5_train_marks.ipynb"
output.write_text(json.dumps(notebook, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(output)
