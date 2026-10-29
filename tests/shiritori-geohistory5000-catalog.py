import sqlite3,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
items=[json.loads(l) for l in (root/'data/geohistory5000/entries.jsonl').read_text(encoding='utf-8').splitlines()]
db=sqlite3.connect('file:'+str(root/'data/entrance-geohistory/catalog.sqlite3')+'?mode=ro',uri=True)
assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert not db.execute('PRAGMA foreign_key_check').fetchall()
for x in items:
 r=db.execute('SELECT reading,word,meaning,origin FROM terms WHERE csv_id=?',(x['id'],)).fetchone()
 assert r==(x['reading'],x['word'],x['meaning'],'geohistory5000'),x['word']
 assert db.execute('SELECT subject FROM topics WHERE csv_id=?',(x['id'],)).fetchone()[0]==x['subject']
assert db.execute("SELECT count(*) FROM terms WHERE origin='geohistory5000'").fetchone()[0]==len(items)
print(json.dumps(dict(passed=True,newCatalogMeanings=len(items),totalCatalogMeanings=db.execute('select count(*) from terms').fetchone()[0])))
