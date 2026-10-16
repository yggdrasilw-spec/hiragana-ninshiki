"""Guard against silently applying editorial row decisions to another CSV."""
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('grade_builder', ROOT / 'scripts/build-shiritori-grade-bands.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
runtime, review = builder.build()
assert len(review) == 12300
assert all(row['status'] == 'assigned' for row in review)
assert runtime == builder.build()[0]

with tempfile.TemporaryDirectory(prefix='shiritori-grades-') as directory:
    root = Path(directory)
    (root / 'data').mkdir()
    (root / 'whitelist.csv').write_bytes((ROOT / 'whitelist.csv').read_bytes())
    original = json.loads((ROOT / 'data/shiritori-grade-decisions.json').read_text(encoding='utf-8'))
    target = root / 'data/shiritori-grade-decisions.json'

    def expect_error(decisions, expected):
        target.write_text(json.dumps(decisions, ensure_ascii=False), encoding='utf-8')
        try:
            builder.build(root)
        except ValueError as error:
            assert expected in str(error), str(error)
        else:
            raise AssertionError('Unsafe decision file was accepted')

    duplicate = json.loads(json.dumps(original))
    duplicate['levels']['2'] += ' ' + duplicate['levels']['1'].split()[0]
    expect_error(duplicate, 'Duplicate grade decision')
    missing = json.loads(json.dumps(original))
    missing['levels']['1'] = ' '.join(missing['levels']['1'].split()[1:])
    expect_error(missing, 'Every dictionary meaning')
    target.write_text(json.dumps(original), encoding='utf-8')
    (root / 'whitelist.csv').write_bytes((root / 'whitelist.csv').read_bytes()+b'\n')
    expect_error(original, 'Dictionary changed')

print(json.dumps({'passed': True, 'assigned': len(review), 'guards': ['duplicate', 'missing', 'changed-dictionary', 'deterministic']}))
