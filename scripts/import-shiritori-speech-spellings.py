"""Import spelling aliases, never game vocabulary or meanings, from JMdict JSON."""
import csv, hashlib, json, pathlib, sys

root = pathlib.Path(__file__).resolve().parent.parent
source = pathlib.Path(sys.argv[1])
raw = source.read_bytes()
data = json.loads(raw)
normalize = lambda s: ''.join(chr(ord(c)-0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)
with (root / 'whitelist.csv').open(encoding='utf-8-sig', newline='') as f:
    known = {row['reading'] for row in csv.DictReader(f)}
aliases = {}
for entry in data['words']:
    common = [k for k in entry['kana'] if k.get('common')]
    for reading in common or entry['kana']:
        if any(t in reading.get('tags', []) for t in ('sk', 'rk', 'ok')):
            continue
        value = normalize(reading['text'])
        if value not in known:
            continue
        for spelling in entry['kanji']:
            if any(t in spelling.get('tags', []) for t in ('sK', 'rK', 'iK', 'oK')):
                continue
            applies = reading.get('appliesToKanji', [])
            if '*' not in applies and spelling['text'] not in applies:
                continue
            aliases.setdefault(spelling['text'], set()).add(value)
out = {'source': {'name': 'JMdict / EDRDG', 'url': 'https://www.edrdg.org/jmdict/j_jmdict.html',
                  'license': 'CC BY-SA 4.0', 'licenseUrl': 'https://creativecommons.org/licenses/by-sa/4.0/',
                  'date': data['dictDate'], 'sha256': hashlib.sha256(raw).hexdigest(),
                  'conversion': 'jmdict-simplified JSON; spellings and readings only; common reading preference, spelling restrictions, existing game readings only'},
       'spellings': {k: sorted(v) for k, v in sorted(aliases.items())}}
(root / 'data/shiritori-speech-spellings.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(f'Imported {len(aliases)} speech spelling aliases')
