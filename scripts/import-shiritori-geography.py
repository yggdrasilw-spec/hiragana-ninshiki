"""Validate staged source evidence and register an independent geography pack.

Does not edit whitelist.csv or its row-bound editorial decisions.
"""
import argparse
import collections
import csv
import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / 'data/dictionary-imports/2026-10-27-japan-geography'
SOURCES = ROOT / 'data/dictionary-imports/japan-geography-sources'
OUT = ROOT / 'data/japan-places'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def hira(text):
    return ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in text)


def validate():
    provenance = json.loads(STAGED.with_suffix('.sources.json').read_text(encoding='utf-8'))
    for name, expected in provenance['snapshots'].items():
        if sha((SOURCES / name).read_bytes()) != expected:
            raise ValueError('Source snapshot changed: ' + name)
    postal = list(csv.DictReader((SOURCES / 'postal-records.csv').open(encoding='utf-8')))
    post = {int(r['record']): r for r in postal}
    stations = {r['code']: r for r in json.loads((SOURCES / 'stations.json').read_text(encoding='utf-8'))}
    prefectures = {int(r['code'][:2]): r['prefecture'] for r in postal}
    staged = json.loads(STAGED.with_suffix('.review.json').read_text(encoding='utf-8'))
    entries = []
    seen = set()
    for r in staged:
        reading, word, category = r['reading'], r['word'], r['category']
        if not re.fullmatch('[ぁ-ゖー]{2,}', reading) or any(c in word for c in ',\n\r"()（）'):
            raise ValueError('Invalid reading/name: ' + reading)
        key = (category, reading, word)
        if key in seen:
            raise ValueError('Duplicate geography sense: ' + reading)
        seen.add(key)
        locations = set()
        for source in r['sources']:
            if source['dataset'] == 'station_database':
                s = stations[source['code']]
                assert category == 'station' and not s['closed']
                assert not s.get('open_date') or s['open_date'] <= '2026-10-28'
                assert word == (s.get('original_name') or s['name']) and reading == hira(s['name_kana'])
                locations.add(prefectures[s['prefecture']])
            elif source.get('derivation'):
                assert source['derivation'] == 'common-city-prefix'
                prefix = os.path.commonprefix(source['municipalities'])
                assert prefix.endswith('シ')
                city = word if category == 'municipality' else word+'市'
                matching = [p for p in postal if p['municipality'].startswith(city) and p['municipality'].endswith('区')]
                assert matching and {p['municipality_kana'] for p in matching} == set(source['municipalities'])
                assert reading == hira(prefix if category == 'municipality' else prefix[:-1])
                locations.update(p['prefecture'] if category == 'municipality' else p['prefecture']+city for p in matching)
            else:
                p = post[source['record']]
                assert source['code'] == p['code'] and source['postal'] == p['postal']
                candidates = []
                if category == 'prefecture':
                    candidates.append((p['prefecture_kana'], p['prefecture'], '日本'))
                elif category == 'town':
                    assert not any(c in p['town']+p['town_kana'] for c in '（）()、，,「」〈〉<>～〜')
                    assert not any(c.isdigit() for c in p['town']+p['town_kana'])
                    assert not any(s in p['town'] for s in ['以下に掲載がない場合', '一円', '次に番地', 'その他'])
                    candidates.append((p['town_kana'], p['town'], p['prefecture']+p['municipality']))
                elif category == 'city-short':
                    assert p['municipality'].endswith('市') and p['municipality_kana'].endswith('シ')
                    candidates.append((p['municipality_kana'][:-1], p['municipality'][:-1], p['prefecture']+p['municipality']))
                elif category == 'municipality':
                    candidates.append((p['municipality_kana'], p['municipality'], p['prefecture']))
                    if '郡' in p['municipality'] and p['municipality_kana'].count('グン') == 1:
                        candidates.append((p['municipality_kana'].split('グン', 1)[1], p['municipality'].split('郡', 1)[1], p['prefecture']+p['municipality'].split('郡', 1)[0]+'郡'))
                    if '市' in p['municipality'] and '区' in p['municipality'] and p['municipality_kana'].count('シ') == 1:
                        candidates.append((p['municipality_kana'].split('シ', 1)[0]+'シ', p['municipality'].split('市', 1)[0]+'市', p['prefecture']))
                matches = [loc for y, w, loc in candidates if hira(y) == reading and w == word]
                assert matches, (category, reading, word, source)
                locations.update(matches)
        assert locations == set(r['locations']), (key, locations, r['locations'])
        # Meanings are rebuilt from validated locations, not the obsolete staged row IDs/CSV level.
        places = sorted(locations)
        loc = '・'.join(places[:3])+('など' if len(places) > 3 else '')
        meaning = ('日本の都道府県の名前。' if category == 'prefecture' else
                   f'{loc}にある鉄道の駅の名前。' if category == 'station' else
                   f'{loc}の市の名前。「市」を付けない呼び方。' if category == 'city-short' else
                   f'{loc}にある市区町村の名前。' if category == 'municipality' else f'{loc}にある地名。')
        assert meaning == r['meaning']
        stable = sha('\t'.join(key).encode())[:24]
        entries.append(dict(id='jp-'+stable, reading=reading, word=word, meaning=meaning,
                            kind=category, locations=places, sources=r['sources'], level=5))
    body = ''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':'))+'\n' for r in entries)
    metadata = dict(schema=1, name='日本の地名・駅名', genre='japanPlace', level=5,
                    entries=len(entries), readings=len({r['reading'] for r in entries}),
                    categories=dict(collections.Counter(r['kind'] for r in entries)),
                    entriesSha256=sha(body.encode()), sourceEvidence=provenance,
                    stagedReviewSha256=sha(STAGED.with_suffix('.review.json').read_bytes()),
                    excluded=json.loads(STAGED.with_suffix('.summary.json').read_text())['excluded'])
    return body, metadata


if __name__ == '__main__':
    args = argparse.ArgumentParser()
    args.add_argument('--write', action='store_true')
    options = args.parse_args()
    body, metadata = validate()
    if options.write:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/'entries.jsonl').write_text(body, encoding='utf-8', newline='\n')
        (OUT/'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(dict(passed=True, written=options.write, entries=metadata['entries'], readings=metadata['readings'], bytes=len(body.encode()))))
