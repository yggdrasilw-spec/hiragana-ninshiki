#!/usr/bin/env python3
"""Build review priority and image fingerprints after vocabulary/image edits."""
import csv
import hashlib
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/image-coverage/review-updates.json'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

def rows(blob):
    return list(csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))))

def text_key(row):
    return tuple(row.get(k, '') for k in ('reading', 'word', 'meaning'))

def assignment_key(row):
    return (*text_key(row), row.get('image_asset', ''))

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def build():
    current = rows((ROOT / 'whitelist.csv').read_bytes())
    previous_catalog = json.loads(OUTPUT.read_text(encoding='utf-8')) if OUTPUT.exists() else {}
    previous_images = previous_catalog.get('images', {})
    previous_text_dates = {tuple(e['text']): e.get('textUpdatedAt', '') for e in previous_catalog.get('entries', [])}
    previous_assignment_dates = {(*e['text'], e.get('image_asset', '')): e.get('imageAssignedAt', '') for e in previous_catalog.get('entries', [])}
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    text_dates = {}
    assignment_dates = {}
    remaining_assignments = {assignment_key(r) for r in current}
    remaining = {text_key(r) for r in current}
    history = git('log', '--format=%H %cI', '--', 'whitelist.csv').decode().splitlines()
    latest = rows(git('show', 'HEAD:whitelist.csv'))
    for key in remaining - {text_key(r) for r in latest}:
        text_dates[key] = now
    remaining -= text_dates.keys()
    for key in remaining_assignments - {assignment_key(r) for r in latest}:
        assignment_dates[key] = now
    remaining_assignments -= assignment_dates.keys()
    for line in history:
        sha, date = line.split(' ', 1)
        changed_rows = rows(git('show', f'{sha}:whitelist.csv'))
        changed = {text_key(r) for r in changed_rows}
        changed_assignments = {assignment_key(r) for r in changed_rows}
        parents = git('rev-list', '--parents', '-n', '1', sha).decode().split()[1:]
        previous = set()
        previous_assignments = set()
        if parents:
            try:
                previous_rows = rows(git('show', f'{parents[0]}:whitelist.csv'))
                previous = {text_key(r) for r in previous_rows}
                previous_assignments = {assignment_key(r) for r in previous_rows}
            except subprocess.CalledProcessError:
                pass  # Initial creation of the CSV.
        for key in remaining & (changed - previous):
            text_dates[key] = date
        remaining -= text_dates.keys()
        for key in remaining_assignments & (changed_assignments - previous_assignments):
            assignment_dates[key] = date
        remaining_assignments -= assignment_dates.keys()
        if not remaining and not remaining_assignments:
            break
    image_dates = {}
    date = ''
    for line in git('log', '--format=@%cI', '--name-only', '--', 'assets/shiritori').decode().splitlines():
        if line.startswith('@'):
            date = line[1:]
        elif line:
            image_dates.setdefault(line, date)
    pending_images = set(git('diff', '--name-only', 'HEAD', '--', 'assets/shiritori').decode().splitlines())
    pending_images.update(git('ls-files', '--others', '--exclude-standard', '--', 'assets/shiritori').decode().splitlines())
    images = {}
    for asset in sorted({r.get('image_asset') for r in current if r.get('image_asset')}):
        blob = (ROOT / asset).read_bytes()
        fingerprint = digest(blob)
        updated = image_dates.get(asset, '')
        previous = previous_images.get(asset, {})
        if previous.get('sha256') == fingerprint:
            updated = previous.get('updatedAt', updated)
        elif previous or asset in pending_images or not updated:
            updated = now
        images[asset] = {'sha256': fingerprint, 'updatedAt': updated}
    entries = [{'id': i + 1, 'text': list(text_key(r)), 'textUpdatedAt': previous_text_dates.get(text_key(r), text_dates.get(text_key(r), '')),
                'image_asset': r.get('image_asset', ''),
                'imageAssignedAt': previous_assignment_dates.get(assignment_key(r), assignment_dates.get(assignment_key(r), '')) if r.get('image_asset') else ''} for i, r in enumerate(current)]
    payload = {'version': 1, 'csvSha256': digest((ROOT / 'whitelist.csv').read_bytes()),
               'entries': entries, 'images': images}
    # No run timestamp: an unchanged tree produces exactly the same catalog.
    payload['revision'] = digest(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Review updates: {len(entries)} words, {len(images)} image fingerprints')

if __name__ == '__main__':
    build()
