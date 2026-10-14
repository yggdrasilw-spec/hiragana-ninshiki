"""Build the individually authored batch against a frozen JMdict source.

Does not modify the live dictionary. Use the existing importer afterwards.
"""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = '2026-10-14-expansion512'
OUT = ROOT / 'data/dictionary-imports'
HEADER = 'reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(',')
BLOCKED = {'arch', 'obs', 'rare', 'obsc', 'vulg', 'sens', 'derog', 'sl', 'X', 'dated'}

def normalize(s):
    return ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in s)

def applies(values, value):
    return '*' in values or value in values

source_path = Path(sys.argv[1])
blob = source_path.read_bytes()
source = json.loads(blob)
assert source['dictDate'] == '2026-10-05', 'Use the reviewed frozen dictionary version.'
assert hashlib.sha256(blob).hexdigest() == '25eb58f942c3847b8379599a687e2c4b194d7eb2bfccfad2eff7be671a11e097', 'Frozen dictionary checksum mismatch.'
index = {}
for entry in source['words']:
    for kana in entry['kana']:
        index.setdefault(normalize(kana['text']), []).append((entry, kana))
existing = list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
summary_file = OUT/(NAME+'.summary.json')
if summary_file.exists():
    # Rebuilding an already imported batch must retain its original IDs and
    # compare against the original prefix, rather than treating itself as old.
    baseline_count = json.loads(summary_file.read_text(encoding='utf-8'))['baselineRows']
    assert len(existing) >= baseline_count
    existing = existing[:baseline_count]
old = {r['reading'] for r in existing}
authored = list(csv.DictReader((OUT/(NAME+'.editorial.tsv')).open(encoding='utf-8'), delimiter='\t'))
rules = []
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#'): continue
    match = re.match(r'^(exact|contains)\s*[:=]\s*(.*)', line, re.I)
    rules.append((match[1].lower(), normalize(match[2].strip())) if match else ('contains',normalize(line)))
rows, reviews, extracts, issues, seen = [], [], [], [], set()
overrides_file = OUT/(NAME+'.sense-overrides.json')
overrides = json.loads(overrides_file.read_text(encoding='utf-8')) if overrides_file.exists() else {}
for row in authored:
    reading, word, meaning = row['reading'], row['word'], row['meaning']
    if reading in old or reading in seen:
        issues.append([reading, word, 'existing-or-duplicate-reading']); continue
    if any(reading==pattern if mode=='exact' else pattern in reading for mode,pattern in rules):
        issues.append([reading,word,'blocked-by-game-rule']);continue
    candidates = []
    for entry, kana in index.get(reading, []):
        forms = [k['text'] for k in entry['kanji'] if applies(kana['appliesToKanji'], k['text'])]
        if word not in forms and word != kana['text']: continue
        for i, sense in enumerate(entry['sense']):
            if not applies(sense['appliesToKana'], kana['text']): continue
            if word in forms and not applies(sense['appliesToKanji'], word): continue
            if set(sense['misc']) & BLOCKED or sense['dialect']: continue
            if not any(p in {'n','num','adj-na','adj-no','vs','vs-i','vs-s','vk'} or p.startswith('v1') or p.startswith('v5') for p in sense['partOfSpeech']): continue
            candidates.append((entry, kana, i, sense))
    if not candidates:
        issues.append([reading, word, 'no-eligible-dictionary-sense']); continue
    # Overrides are explicit editorial decisions after reading the source senses.
    override = overrides.get(reading)
    if override:
        candidates = [c for c in candidates if c[0]['id'] == override['entryId'] and c[2] == override['senseIndex']]
        if not candidates:
            raise ValueError('Invalid explicit sense: '+reading)
    entry, kana, sense_index, sense = candidates[0]
    assert re.fullmatch('[ぁ-ゖー]{2,}', reading) and not reading.endswith('ん'), reading
    assert meaning.endswith('。') and not re.search('[,\r\n]', meaning), reading
    level = int(row['level'])
    assert level in (1,2,3)
    if level == 1: assert not re.search('[\u3400-\u9fff]',meaning), reading
    rows.append([reading,word,meaning,word,str(level),'','','',''])
    url = 'https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+entry['id']
    reviews.append(dict(id=len(existing)+len(rows), reading=reading, word=word, meaning=meaning, level=level,
        entryId=entry['id'], sourceKana=kana['text'], senseIndexes=[sense_index], partOfSpeech=sense['partOfSpeech'],
        lexicalSource=f"JMdict {entry['id']} / {source['dictDate']} / {url}", sources=[url],
        meaningReason='対象語義の動作・用途・状態を区別して独自説明を作成。'+meaning,
        ageReason=('身近な行動・物・状態をかなの具体的説明で示せる。' if level==1 else '学習語や改まった表現として、概要を具体的に説明する。'),
        reviewStatus='editorially-reviewed', definitionAuthor='独自作成（2026-10-14）', imageStatus='not-created',
        imageReason='今回は保存画像を追加しない。既存の外部検索・プレースホルダーを利用し、検索画像の意味一致は未確認。'))
    supplemental = {
        'おしべ':'https://www.dainippon-tosho.co.jp/yagi/1996/960915/3.html',
        'めしべ':'https://kids.gakken.co.jp/kagaku/kagaku110/science0242/',
        'いおう':'https://apec.aichi-c.ed.jp/kyouka/rika/kagaku/2018/muki/iou/iou.htm'
    }
    if reading in supplemental: reviews[-1]['sources'].append(supplemental[reading])
    extracts.append(dict(reading=reading,word=word,entryId=entry['id'],sourceKana=kana['text'],senseIndex=sense_index,
        kanaAppliesToKanji=kana['appliesToKanji'],appliesToKana=sense['appliesToKana'],appliesToKanji=sense['appliesToKanji'],
        partOfSpeech=sense['partOfSpeech'],misc=sense['misc'],dialect=sense['dialect']))
    seen.add(reading)
    if '--inspect' in sys.argv:
        print(reading+'|'+word+'|'+str(sense_index)+'|'+'; '.join(g['text'] for g in sense['gloss'] if g['lang']=='eng'))
if '--inspect' in sys.argv:
    print(json.dumps({'eligible':len(rows),'issues':issues},ensure_ascii=False));sys.exit()
assert len(rows)==512, f'Need exactly 512 eligible authored words: {len(rows)}; issues={issues}'
assert not issues, issues
with (OUT/(NAME+'.csv')).open('w',encoding='utf-8',newline='') as f:
    writer=csv.writer(f,lineterminator='\n');writer.writerow(HEADER);writer.writerows(rows)
def save(name, obj):
    (OUT/(NAME+name)).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
save('.review.json',reviews)
save('.source.json',dict(dictDate=source['dictDate'],version=source['version'],sourceSha256=hashlib.sha256(blob).hexdigest(),
    attribution='James William BREEN / Electronic Dictionary Research and Development Group',license='CC BY-SA 4.0',
    licenseUrl='https://www.edrdg.org/edrdg/licence.html',rows=extracts))
print(json.dumps({'reviewed':len(rows),'levels':{str(n):sum(r[4]==str(n) for r in rows) for n in (1,2,3)}},ensure_ascii=False))
