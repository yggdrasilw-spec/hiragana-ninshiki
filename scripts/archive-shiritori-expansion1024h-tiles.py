"""Preserve superseded, unregistered crops before a reviewed replacement."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/image-coverage/2026-10-18-expansion1024h'
p = argparse.ArgumentParser()
p.add_argument('--sheet', type=int, required=True)
a = p.parse_args()
report = json.loads((OUT / f'sheet{a.sheet:02}-crop.json').read_text(encoding='utf-8'))
dest = OUT / 'superseded' / f'sheet{a.sheet:02}'
registered = {x['file'] for x in json.loads((ROOT / 'assets/shiritori/manifest.json').read_text(encoding='utf-8'))['assets']}
for tile in report['tiles']:
    name = tile['file']
    assert name not in registered, 'Never move registered assets'
    source = ROOT / 'assets/shiritori' / name
    target = dest / name
    assert source.resolve().is_relative_to(ROOT) and target.resolve().is_relative_to(ROOT)
    assert source.is_file() and not target.exists()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == tile['sha256']
dest.mkdir(parents=True, exist_ok=True)
for tile in report['tiles']:
    shutil.move(str(ROOT / 'assets/shiritori' / tile['file']), str(dest / tile['file']))
print(f'Preserved {len(report["tiles"])} superseded crops in {dest}')
