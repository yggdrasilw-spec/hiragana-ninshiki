"""Inventory images without changing dictionary paths or image provenance."""
import argparse
import csv
import hashlib
import json
import mimetypes
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif', '.avif', '.ico', '.bmp', '.tif', '.tiff'}

def inventory():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    paths = {ROOT / p for p in tracked if Path(p).suffix.lower() in EXTENSIONS}
    paths.add(ROOT / 'shiritori_title.png')
    for folder in ['assets/shiritori', 'data/image-coverage']:
        paths.update(p for p in (ROOT / folder).rglob('*') if p.is_file() and p.suffix.lower() in EXTENSIONS)
    entries = []
    for path in sorted(paths):
        if not path.is_file():
            raise RuntimeError(f'Missing tracked image: {path}')
        key = path.relative_to(ROOT).as_posix()
        public = key == 'shiritori_title.png' or path.parent == ROOT / 'assets/shiritori'
        entries.append({'key': key, 'bucket': 'shiritori-images' if public else 'shiritori-image-archive', 'bytes': path.stat().st_size, 'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest(), 'contentType': mimetypes.guess_type(key)[0] or 'application/octet-stream'})
    references = {r['image_asset'] for r in csv.DictReader((ROOT / 'whitelist.csv').open(encoding='utf-8-sig')) if r.get('image_asset')}
    public_keys = {e['key'] for e in entries if e['bucket'] == 'shiritori-images'}
    missing = sorted(references - public_keys)
    if missing:
        raise RuntimeError(f'Dictionary images missing: {missing}')
    revision = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()
    return {'version': 1, 'revision': revision, 'dictionaryImageReferences': len(references), 'entries': entries}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = inventory()
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(dest), 'revision': data['revision'], 'dictionaryImages': data['dictionaryImageReferences'], 'buckets': {bucket: {'files': sum(e['bucket'] == bucket for e in data['entries']), 'bytes': sum(e['bytes'] for e in data['entries'] if e['bucket'] == bucket)} for bucket in ['shiritori-images', 'shiritori-image-archive']}}))
