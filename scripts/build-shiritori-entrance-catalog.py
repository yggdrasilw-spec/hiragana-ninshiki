"""Build a searchable local SQLite catalog; JSONL is the versioned editorial source.

No DB or whole catalog is downloaded by the game. --output allows rebuilding elsewhere.
"""
import argparse,collections,csv,hashlib,io,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CAT=ROOT/'data/entrance-geohistory'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=CAT/'catalog.sqlite3');args=parser.parse_args()
 csvbytes=(ROOT/'whitelist.csv').read_bytes();rows=list(csv.DictReader(io.StringIO(csvbytes.decode('utf-8'))))
 lookup=collections.defaultdict(list)
 for i,r in enumerate(rows,1):lookup[(r['reading'],r['word'])].append((i,r))
 corpus=[json.loads(l) for l in (CAT/'entries.jsonl').read_text(encoding='utf-8').splitlines()]
 entries={}
 for x in corpus:
  matches=lookup[(x['reading'],x['word'])] if x['status']=='add' else [(i,rows[i-1]) for i in x['existingIds']]
  assert matches,x['word']
  assert all(r['reading']==x['reading'] for _,r in matches),x['word']
  for i,r in matches:entries[i]=dict(csvId=i,**r,topics=x['topics'],catalogId=x['catalogId'],origin='entrance-corpus',lexicalEvidence='JMdict-form' if x['dictionaryEntries'] else 'editorial',senseChecked=x['status']=='add')
 previous=ROOT/'data/dictionary-imports/2026-10-28-geohistory2000.review.json'
 for x in json.loads(previous.read_text(encoding='utf-8')):
  for i,r in lookup[(x['reading'],x['word'])]:
   if i in entries:continue
   cat=x['category'];subject='日本史' if '日本史' in cat else '世界史' if any(t in cat for t in ['世界史','中国史']) else '地理'
   entries[i]=dict(csvId=i,**r,topics=[subject+'/先行収録：'+cat],catalogId='prior-'+str(i),origin='geohistory2000',lexicalEvidence='prior-editorial',senseChecked=False)
 # Rebuild only the generated destination. Leave unrelated files untouched.
 args.output.parent.mkdir(parents=True,exist_ok=True)
 if args.output.exists():args.output.unlink()
 db=sqlite3.connect(args.output)
 with db:
  db.executescript('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL); CREATE TABLE terms(csv_id INTEGER PRIMARY KEY,catalog_id TEXT NOT NULL,reading TEXT NOT NULL,word TEXT NOT NULL,meaning TEXT NOT NULL,origin TEXT NOT NULL,evidence TEXT NOT NULL,sense_checked INTEGER NOT NULL); CREATE TABLE topics(csv_id INTEGER NOT NULL,subject TEXT NOT NULL,topic TEXT NOT NULL,PRIMARY KEY(csv_id,subject,topic),FOREIGN KEY(csv_id) REFERENCES terms(csv_id)); CREATE INDEX terms_reading ON terms(reading); CREATE INDEX terms_word ON terms(word); CREATE INDEX topics_subject ON topics(subject,topic);')
  db.executemany('INSERT INTO metadata VALUES (?,?)',[('dictionarySha256',hashlib.sha256(csvbytes).hexdigest()),('scope','高校地理歴史の拡充台帳。大学受験全語の網羅を保証しない。')])
  for i,x in sorted(entries.items()):
   db.execute('INSERT INTO terms VALUES(?,?,?,?,?,?,?,?)',(i,x['catalogId'],x['reading'],x['word'],x['meaning'],x['origin'],x['lexicalEvidence'],x['senseChecked']))
   for topic in x['topics']:
    subject,name=topic.split('/',1);db.execute('INSERT OR IGNORE INTO topics VALUES(?,?,?)',(i,subject,name))
  assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  counts=[dict(subject=s,topic=t,terms=n) for s,t,n in db.execute('SELECT subject,topic,count(*) FROM topics GROUP BY subject,topic ORDER BY subject,topic')]
  summary=dict(dictionarySha256=hashlib.sha256(csvbytes).hexdigest(),dictionaryRows=len(rows),indexedMeanings=len(entries),curatedChecklistTerms=len(corpus),topics=counts,coverageStatus='拡充中・全教科書全入試の網羅照合は未実施',limitations=['既存語の一致は読み・表記の照合。既存説明の全件再校閲ではない。','科目資料は範囲確認。専門語の全件を独立辞書で個別照合したものではない。','SQLiteは管理・検索用。ゲームは既存の分割JSON配信を使う。'])
  # Alternate output is useful for read-only validation without rewriting repository reports.
  if args.output==CAT/'catalog.sqlite3':(CAT/'coverage.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 db.close();print(json.dumps({k:v for k,v in summary.items() if k!='topics'},ensure_ascii=False))
if __name__=='__main__':main()
