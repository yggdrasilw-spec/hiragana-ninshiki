"""Append the documented entertainment intake and rebuild its derived indexes."""
import csv,json,hashlib,subprocess,sys,shutil
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-29-manga1000'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def main():
 s=read(BASE.with_suffix('.summary.json'));items=read(BASE.with_suffix('.review.json'))
 if s['registered']:
  print(json.dumps(dict(alreadyRegistered=True,added=len(items))));return
 before=(ROOT/'whitelist.csv').read_bytes();assert sha(before)==s['beforeSha256'],'Concurrent dictionary edit'
 old=list(csv.DictReader(before.decode('utf-8').splitlines()));assert len(old)==s['baselineRows']
 dfile=ROOT/'data/shiritori-grade-decisions.json';d=read(dfile)
 cfile=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(cfile)
 ufile=ROOT/'data/image-coverage/review-updates.json';updates=read(ufile)
 assert d['sourceSha256']==sha(before) and d['reviewedRows']==len(old)
 assert len(coverage)==len(old) and updates['csvSha256']==sha(before) and len(updates['entries'])==len(old)
 node=shutil.which('node');assert node
 def run(*args):subprocess.run(args,cwd=ROOT,check=True)
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
 if '--import-reviewed' not in sys.argv:return
 assert (ROOT/'whitelist.csv').read_bytes()==before
 run(node,'scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
 after=(ROOT/'whitelist.csv').read_bytes();assert after.startswith(before)
 assert len(after.splitlines())-1==len(old)+len(items)
 now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 for x in items:
  d['levels']['5']+=' '+str(x['id']-1);d.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
  coverage.append(dict(id=x['id'],reading=x['reading'],word=x['word'],meaning=x['meaning'],level='3',image_asset='',category=x['category'],target=True,scopeReason='漫画の作品名と作者・原作者・作画担当を出典付きで追加。',status='explanation-only',assignment='none',originalId=None))
  updates['entries'].append(dict(id=x['id'],text=[x['reading'],x['word'],x['meaning']],textUpdatedAt=now,image_asset='',imageAssignedAt=''))
 d.update(sourceSha256=sha(after),reviewedRows=len(old)+len(items));save(dfile,d)
 run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py');save(cfile,coverage)
 updates['csvSha256']=sha(after);updates.pop('revision',None);updates['revision']=sha(json.dumps(updates,ensure_ascii=False,sort_keys=True).encode())
 ufile.write_text(json.dumps(updates,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8',newline='\n')
 s.update(registered=True,afterSha256=sha(after),totalRows=len(old)+len(items),explanationOnly=len(items))
 save(BASE.with_suffix('.summary.json'),s);print(json.dumps(s,ensure_ascii=False))
if __name__=='__main__':main()
