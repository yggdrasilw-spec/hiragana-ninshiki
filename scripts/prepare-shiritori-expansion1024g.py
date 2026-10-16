"""Prepare a separate reviewed vocabulary batch; never mutate the live dictionary."""
import csv, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = '2026-10-16-expansion1024g'
OUT = ROOT / 'data/image-coverage' / NAME
OUT.mkdir(parents=True, exist_ok=True)
if (OUT/'plan.json').exists():
    raise SystemExit('The registration plan is frozen. Keep its draft and reservation unchanged.')
IMPORTS = ROOT / 'data/dictionary-imports'
SOURCE = Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json')
norm = lambda s: ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in s)
def save(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if 'reading' in k.lower() and isinstance(v, str):
                yield norm(v)
            else:
                yield from strings(v)
    elif isinstance(obj, list):
        for v in obj: yield from strings(v)

baseline = OUT / 'baseline.csv'
if not baseline.exists(): baseline.write_bytes((ROOT/'whitelist.csv').read_bytes())
live = list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')))
existing = {x['reading'] for x in live}
exclusions = set()
analysis = Path('C:/Users/user/.codex/artifacts/shiritori-gas-analysis-2026-10-16/analysis.json')
if analysis.exists(): exclusions.update(strings(json.loads(analysis.read_text(encoding='utf-8'))))
for p in IMPORTS.glob('*.review.json'):
    if NAME not in p.name: exclusions.update(strings(json.loads(p.read_text(encoding='utf-8'))))
for p in (ROOT/'data/image-coverage').glob('*/reservation.json'):
    if NAME not in str(p): exclusions.update(strings(json.loads(p.read_text(encoding='utf-8'))))
blocked=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
    line=line.strip()
    if not line or line.startswith('#'): continue
    m=re.match(r'^(exact|contains)\s*[:=]\s*(.*)', line, re.I)
    blocked.append((m[1].lower(), norm(m[2])) if m else ('contains', norm(line)))
blob=SOURCE.read_bytes(); source=json.loads(blob); index={}
for entry in source['words']:
    for kana in entry['kana']: index.setdefault(norm(kana['text']), []).append((entry, kana))
items=[]; skipped=[]; issues=[]; seen=set()
for line in (IMPORTS/(NAME+'.editorial.txt')).read_text(encoding='utf-8').splitlines():
    if not line.strip() or line.startswith('#'): continue
    rd, word, meaning = line.split('|')[:3]
    reason = 'existing' if rd in existing else 'other-batch-reserved' if rd in exclusions else 'duplicate' if rd in seen else None
    if reason: skipped.append(dict(reading=rd,word=word,reason=reason)); continue
    if not re.fullmatch('[ぁ-ゖー]+',rd) or rd.endswith('ん'):
        skipped.append(dict(reading=rd,word=word,reason='unplayable')); continue
    if any(rd==s if mode=='exact' else s in rd for mode,s in blocked):
        skipped.append(dict(reading=rd,word=word,reason='blacklist')); continue
    candidates=[]
    for entry,k in index.get(rd,[]):
        if k['tags']: continue
        forms=[x['text'] for x in entry['kanji'] if not x['tags'] and ('*' in k['appliesToKanji'] or x['text'] in k['appliesToKanji'])]
        if word not in forms and word!=k['text']: continue
        for si,s in enumerate(entry['sense']):
            if set(s['misc']) & {'arch','obs','rare','obsc','vulg','sens','derog','sl','X','dated'} or s['dialect']: continue
            if '*' not in s['appliesToKana'] and k['text'] not in s['appliesToKana']: continue
            if '*' not in s['appliesToKanji'] and word not in s['appliesToKanji']: continue
            candidates.append((entry,k,si,s))
    if not candidates:
        issues.append(dict(reading=rd,word=word,reason='no-applicable-entry')); continue
    entry,k,si,s=candidates[0]
    seen.add(rd)
    url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e='+entry['id']
    items.append(dict(reading=rd,word=word,meaning=meaning,level=2,entryId=entry['id'],sourceKana=k['text'],senseIndex=si,
        partOfSpeech=s['partOfSpeech'],lexicalSource=f"JMdict {entry['id']} / {source['dictDate']} / {url}",sources=[url],
        meaningReason='選択した見出しの意味を具体的な日本語で独自に説明。'+meaning,
        ageReason='小学校の生活・読書・学習で意味を説明できる語を選定。漢字や抽象的な内容を含むためレベル2。',
        definitionAuthor='独自作成（2026-10-16）',reviewStatus='meaning-review-pending',
        kanaAppliesToKanji=k['appliesToKanji'],appliesToKana=s['appliesToKana'],appliesToKanji=s['appliesToKanji']))
save(OUT/'reservation.json',dict(batch=NAME,status='preparing',excludedOtherReadings=sorted(exclusions-existing),items=[dict(reading=x['reading'],word=x['word']) for x in items]))
save(OUT/'draft.json',dict(batch=NAME,baselineRows=len(live),baselineSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest(),
    sourceSha256=hashlib.sha256(blob).hexdigest(),sourceDate=source['dictDate'],items=items,skipped=skipped,issues=issues))
print(json.dumps(dict(eligible=len(items),skipped=len(skipped),issues=issues,existing=[x['reading'] for x in skipped if x['reason']=='existing']),ensure_ascii=False))
