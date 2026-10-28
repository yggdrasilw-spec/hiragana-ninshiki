"""Build an indexed, editor-only science catalogue. Never downloaded at startup."""
import csv,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
 review=json.loads((ROOT/'data/dictionary-imports/2026-10-28-science.review.json').read_text(encoding='utf-8'))
 target=ROOT/'data/science/catalog.sqlite';temporary=target.with_suffix('.building.sqlite')
 if temporary.exists():temporary.unlink()
 db=sqlite3.connect(temporary)
 db.executescript('CREATE TABLE entries(id INTEGER PRIMARY KEY,reading TEXT NOT NULL,word TEXT NOT NULL,meaning TEXT NOT NULL,subject TEXT NOT NULL,unit TEXT,core INTEGER NOT NULL,source_kind TEXT NOT NULL,source_url TEXT NOT NULL,generated INTEGER NOT NULL,level INTEGER NOT NULL CHECK(level=5)); CREATE INDEX by_reading ON entries(reading); CREATE INDEX by_word ON entries(word); CREATE INDEX by_subject ON entries(subject,reading); CREATE VIRTUAL TABLE search USING fts5(word,reading,meaning,content=entries,content_rowid=id,tokenize="trigram");')
 for x in review:
  db.execute('INSERT INTO entries VALUES(?,?,?,?,?,?,?,?,?,?,?)',(x['id'],x['reading'],x['word'],x['meaning'],x['category'],x.get('unit'),int(x.get('core',False)),x['source']['kind'],x['source']['url'],int(x['source'].get('generated',False)),5))
 db.execute("INSERT INTO search(search) VALUES('rebuild')");db.commit()
 assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
 assert db.execute('SELECT count(*) FROM entries').fetchone()[0]==len(review)
 db.close();temporary.replace(target);print(json.dumps(dict(catalogue=True,entries=len(review),bytes=target.stat().st_size)))
if __name__=='__main__':build()
