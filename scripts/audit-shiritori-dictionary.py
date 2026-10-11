"""Compare a local jmdict-simplified JSON with the app; never copy glosses.

Usage: python scripts/audit-shiritori-dictionary.py /tmp/jmdict-eng-3.6.2.json --output /tmp/audit
"""
import argparse
import collections
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LICENSE = 'https://www.edrdg.org/edrdg/licence.html'
BLOCKED = {'arch', 'obs', 'rare', 'obsc', 'vulg', 'sens', 'derog', 'sl', 'X'}


def normalize(text):
    text = unicodedata.normalize('NFKC', text)
    return ''.join(chr(ord(c) - 96) if 'ァ' <= c <= 'ヶ' else c for c in text)


def applies(values, text):
    return '*' in values or text in values


def pairs(entry):
    """Respect reading and sense restrictions, including kana-only readings."""
    for kana in entry['kana']:
        forms = [k for k in entry['kanji'] if applies(kana['appliesToKanji'], k['text'])]
        if not forms:
            forms = [kana]
        for form in forms:
            senses = [s for s in entry['sense']
                      if applies(s['appliesToKana'], kana['text'])
                      and (form is kana or applies(s['appliesToKanji'], form['text']))]
            if senses:
                yield kana, form, senses


def audit(dictionary, rows):
    index = collections.defaultdict(set)
    entries = collections.defaultdict(set)
    candidates = []
    existing_pairs = {(normalize(r['reading']), normalize(r['word'])) for r in rows}
    existing_readings = {normalize(r['reading']) for r in rows}
    filtered = collections.Counter()
    for entry in dictionary['words']:
        for kana, form, senses in pairs(entry):
            reading, word = normalize(kana['text']), form['text']
            index[normalize(word)].add(reading)
            index[reading].add(reading)
            entries[(reading, normalize(word))].add(entry['id'])
            entries[(reading, reading)].add(entry['id'])
            if (reading, normalize(word)) in existing_pairs:
                continue
            reason = None
            noun_senses = [s for s in senses if 'n' in s['partOfSpeech']]
            if not re.fullmatch('[ぁ-ゖー]{2,12}', reading) or reading.startswith('ー'):
                reason = 'reading-format-or-length'
            elif reading.endswith('ん'):
                reason = 'ends-in-n'
            elif not (kana['common'] or form['common']):
                reason = 'not-common'
            elif form['tags'] or kana['tags']:
                reason = 'marked-spelling-or-reading'
            elif not noun_senses:
                reason = 'not-noun'
            elif all(set(s['misc']) & BLOCKED or s['dialect'] for s in noun_senses):
                reason = 'marked-sense'
            elif any(c in word for c in ',\r\n'):
                reason = 'unsupported-csv'
            if reason:
                filtered[reason] += 1
                continue
            candidates.append({'entryId': entry['id'], 'reading': reading, 'word': word,
                               'status': 'existing-reading-review' if reading in existing_readings else 'new-reading-review',
                               'source': 'https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e=' + entry['id']})
    covered = {(entry_id, reading) for reading, word in existing_pairs
               for entry_id in entries.get((reading, word), set())}
    # Alternative spellings in the same entry and reading are not new vocabulary.
    candidates = [c for c in candidates if not
                  (c['entryId'], c['reading']) in covered]
    unique = {(c['entryId'], c['reading'], c['word']): c for c in candidates}
    candidates = sorted(unique.values(), key=lambda c: (c['reading'], c['entryId'], c['word']))
    matches, unlisted, mismatches = 0, [], []
    for ident, row in enumerate(rows, 1):
        readings = index.get(normalize(row['word']), set())
        item = {'id': ident, 'reading': row['reading'], 'word': row['word']}
        if normalize(row['reading']) in readings:
            matches += 1
        elif readings:
            mismatches.append({**item, 'dictionaryReadings': sorted(readings)})
        else:
            unlisted.append(item)
    return {'dictionaryEntries': len(dictionary['words']), 'vocabularyRows': len(rows),
            'matchedRows': matches, 'unlisted': unlisted, 'readingMismatches': mismatches,
            'candidatePairs': len(candidates), 'candidateReadings': len({c['reading'] for c in candidates}),
            'candidateCounts': dict(collections.Counter(c['status'] for c in candidates)),
            'filteredPairs': dict(filtered)}, candidates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dictionary', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-url', required=True)
    args = parser.parse_args()
    raw = args.dictionary.read_bytes()
    dictionary = json.loads(raw)
    if dictionary.get('commonOnly') is not False:
        parser.error('Use the complete dictionary to avoid misleading unlisted results.')
    with (ROOT / 'whitelist.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    report, candidates = audit(dictionary, rows)
    report['source'] = {'name': 'JMdict / jmdict-simplified', 'date': dictionary['dictDate'],
                        'version': dictionary['version'], 'url': args.source_url,
                        'sha256': hashlib.sha256(raw).hexdigest(), 'license': LICENSE,
                        'attribution': 'James William BREEN and the Electronic Dictionary Research and Development Group',
                        'derivedDataLicense': 'CC-BY-SA-4.0'}
    report['vocabularySha256'] = hashlib.sha256((ROOT / 'whitelist.csv').read_bytes()).hexdigest()
    report['limitations'] = '未収録は誤りの証明ではない。候補は子ども向けの語義・年齢・表記・画像を未レビュー。commonは低学年向けの意味ではない。語義・例文は出力しない。'
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    with (args.output / 'candidates.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['entryId', 'reading', 'word', 'status', 'source'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(candidates)
    print(json.dumps({k: report[k] for k in ['dictionaryEntries', 'vocabularyRows', 'matchedRows', 'candidatePairs', 'candidateReadings', 'candidateCounts']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
