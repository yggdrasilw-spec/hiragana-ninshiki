"""Append the reviewed 875-word supplement, preserving the earlier 149 words.

All decisions and catalog entries are preflighted against an exact dictionary
hash. The existing reviewed importer performs the actual append and history.
"""
import argparse,collections,csv,hashlib,json,os,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-25-seven-categories1024'
INITIAL=ROOT/'data/dictionary-imports/2026-10-25-seven-categories.review.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--import-reviewed',action='store_true');args=parser.parse_args()
 summary=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'));initial=read(INITIAL)
 assert len(initial)==149 and len(items)==875 and len(initial+items)==1024
 before=(ROOT/'whitelist.csv').read_bytes();old=list(csv.DictReader(before.decode('utf-8').splitlines()))
 if summary.get('registered'):
  assert all(all(old[x['id']-1][k]==str(x[k]) for k in ('reading','word','meaning')) for x in initial+items)
  print(json.dumps(dict(alreadyRegistered=True,totalAdded=1024,totalRows=len(old))));return
 assert sha(before)==summary['beforeSha256'] and len(old)==15699,'Dictionary baseline changed'
 decisionsfile=ROOT/'data/shiritori-grade-decisions.json';decisions=read(decisionsfile)
 coveragefile=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragefile)
 updatesfile=ROOT/'data/image-coverage/review-updates.json';updates=read(updatesfile)
 assert decisions['sourceSha256']==sha(before) and decisions['reviewedRows']==len(old)
 assert len(coverage)==len(old) and updates['csvSha256']==sha(before) and len(updates['entries'])==len(old)
 assert [x['id'] for x in items]==list(range(len(old)+1,len(old)+876))
 for x in initial:assert all(old[x['id']-1][k]==str(x[k]) for k in ('reading','word','meaning'))
 node=shutil.which('node') or str(Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe')
 def run(*args):subprocess.run(args,cwd=ROOT,check=True)
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 if not args.import_reviewed:print(json.dumps(dict(validated=True,supplement=875,totalAdded=1024)));return
 assert (ROOT/'whitelist.csv').read_bytes()==before,'Concurrent dictionary edit'
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(ROOT/'whitelist.csv').read_bytes();assert after.startswith(before)
 afterrows=list(csv.DictReader(after.decode('utf-8').splitlines()));assert len(afterrows)==16574
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 for x in items:
  decisions['levels'][str(x['grade'])]+=' '+str(x['id']-1);decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
  coverage.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],level=str(x['level']),image_asset='',category=x['category'],target=True,scopeReason='利用者指定の7分野を、先行149語と合わせて1024項目へ拡充。',status='explanation-only',assignment='none',originalId=None))
  updates['entries'].append(dict(id=x['id'],text=[x['reading'],x['word'],x['meaning']],textUpdatedAt=now,image_asset='',imageAssignedAt=''))
 decisions.update(sourceSha256=sha(after),reviewedRows=len(afterrows));save(decisionsfile,decisions)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');save(coveragefile,coverage)
 updates['csvSha256']=sha(after);updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 updatesfile.write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 summary.update(registered=True,afterSha256=sha(after),totalRows=16574,totalAdded=1024,baselineBeforeInitial=15550,explanationOnly=1024,newReadingsIncludingInitial=149+summary['newReadings'])
 save(BASE.with_suffix('.summary.json'),summary)
 print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':main()
