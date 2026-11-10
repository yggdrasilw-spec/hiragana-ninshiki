"""Export the browser application and its referenced data for GitHub Pages."""

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / '_site'
if OUTPUT.exists():
    raise SystemExit(f'Refusing to overwrite an existing export: {OUTPUT}')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


tracked = set(git('ls-files', '-z').decode().split('\0')) - {''}
runtime = {name for name in tracked if '/' not in name and
           (Path(name).suffix in {'.html', '.js', '.mjs', '.css', '.wav', '.mp3', '.svg', '.png', '.ico'}
            or name in {'whitelist.csv', 'blacklist.txt', '.nojekyll', 'CNAME'})}
runtime.update(name for name in tracked if name.startswith('tfjs_model/'))
runtime.update(name for name in tracked if name.startswith('assets/') and
               not name.startswith(('assets/shiritori/sheets/', 'assets/shiritori/manifest-data/')))
manifest = json.loads((ROOT / 'assets/shiritori/manifest.json').read_text(encoding='utf-8-sig'))
if manifest.get('manifestVersion') == 2:
    for shards in manifest['shards'].values():
        runtime.update('assets/shiritori/' + name for name in shards)

runtime.update({
    'data/kana-feedback-reference.json',
    'data/shiritori-speech-readings.json',
    'data/image-coverage/review-2026-10-10.json',
    'data/image-coverage/review-updates.json',
    'data/batches/2026-10-11-jmdict.csv',
    'data/general10000/wordnet-LICENSE.txt',
    'data/onomatopoeia/NOTICE.md',
})
runtime.update(name for name in tracked if name.startswith('data/') and
               any(tag in Path(name).name.upper() for tag in ('LICENSE', 'NOTICE')))

# Keep the current indexes, plus chunks used by the previous two distinct
# published indexes, so an already-open browser can finish its current game.
for base in ('data/shiritori-delivery/', 'data/shiritori-delivery/japan-places/'):
    index_path = base + 'index.json'
    runtime.add(index_path)
    revisions = git('log', '-3', '--format=%H', '--', index_path).decode().splitlines()
    for revision in revisions:
        index = json.loads(git('show', revision + ':' + index_path))
        runtime.update(base + item['file'] for item in index['chunks'])

missing = runtime - tracked
if missing:
    raise SystemExit(f'Runtime files are missing from Git: {sorted(missing)}')
for name in sorted(runtime):
    source = ROOT / name
    if source.is_symlink() or not source.is_file():
        raise SystemExit(f'Runtime file must be a regular file: {name}')
    destination = OUTPUT / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

size = sum((OUTPUT / name).stat().st_size for name in runtime)
print(json.dumps({'files': len(runtime), 'bytes': size, 'output': str(OUTPUT)}))
