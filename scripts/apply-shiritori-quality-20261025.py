"""Apply the reviewed 2026-10-25 image replacements; default is validation only."""
import argparse,csv,hashlib,importlib.util,io,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/image-coverage/2026-10-25-quality'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
 plan=read(BASE/'plan.json'); baseline=read(BASE/'baseline.json');csvpath=ROOT/'whitelist.csv';before=csvpath.read_bytes();mp=ROOT/'assets/shiritori/manifest.json'
 ledger=BASE/'applied.json'
 if ledger.exists():
  record=read(ledger);assert sha(before)==record['afterSha256'];assert sha(mp.read_bytes())==record['manifestAfterSha256'];assert all(sha((ROOT/'assets/shiritori'/e['afterFile']).read_bytes())==e['afterSha256'] for e in record['edits']);print('Already applied; baseline and image checks passed.');return
 assert sha(before)==baseline['dictionarySha256'],'Dictionary changed; rebase the reviewed plan first.'
 assert sha(mp.read_bytes())==baseline['manifestSha256'],'Manifest changed; rebase the reviewed plan first.'
 text=before.decode('utf-8-sig');reader=csv.DictReader(io.StringIO(text));fields=reader.fieldnames;rows=list(reader);manifest=read(mp);assets={a['file']:a for a in manifest['assets']}
 review=read(BASE/'semantic-review.json');assert review['approved'] is True
 assert set(review['files'])=={a['file'] for a in plan}
 spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
 validated={};replacements={};edits=[]
 for a in plan:
  old=a['file'];assert sha((ROOT/'assets/shiritori'/old).read_bytes())==a['beforeSha256'];assert assets[old]==a['beforeMetadata']
  sn=a['sheet'];sheet=f'sheets/quality-20261025-sheet{sn:02}.png';report=f'data/image-coverage/2026-10-25-quality/sheet{sn:02}-crop.json'
  if sn not in validated:validated[sn]=grid.verify_report(ROOT/report,ROOT/'assets/shiritori'/sheet,BASE/'tiles')
  primary=a['words'][0];filename=f'quality-20261025-word-{primary["id"]}.png';evidence=validated[sn][filename];assert evidence['tileIndex']==a['tileIndex']
  actual=[dict(id=i,**{k:r[k] for k in ('reading','word','meaning')}) for i,r in enumerate(rows,1) if r.get('image_asset')=='assets/shiritori/'+old]
  assert actual==a['words'],'Shared senses changed.'
  aliases=[];previous={v['id']:v for v in assets[old].get('aliases',[])}
  for w in actual:
   al=dict(previous.get(w['id'],{}));al.update(w,reuseReason='元の共有先全語義を維持し、再生成画像との対応を確認。',sourceReview=review['files'][old]);aliases.append(al)
  new={k:v for k,v in assets[old].items() if k not in ('cropBox','cropChecks','sheetSize','grid','cropValidation','cropMethod','sha256','sourceType','integration')}
  new.update(**{k:primary[k] for k in ('reading','word','meaning')},file=old,mode=assets[old]['mode'],credit=assets[old]['credit'],generatedAt='2026-10-25',lastCorrectedAt='2026-10-25',sourceSheet=sheet,tileIndex=a['tileIndex'],prompt=(BASE/f'sheet{sn:02}.prompt.txt').read_text(encoding='utf-8'),cropValidation=report,cropBox=evidence['cropBox'],cropChecks=evidence,cropMethod=read(ROOT/report)['method'],sha256=evidence['sha256'],aliases=aliases,status='reviewed',review=review['files'][old],validatedTile=filename,replacesSha256=a['beforeSha256'],correctionReason=a['reason'])
  replacements[old]=new;edits.append(dict(beforeFile=old,afterFile=old,validatedTile=filename,beforeSha256=a['beforeSha256'],afterSha256=evidence['sha256'],ids=[w['id'] for w in actual],reason=a['reason']))
 stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows);after=stream.getvalue().encode('utf-8')
 historypath=ROOT/'data/dictionary-imports/history.json';history=read(historypath);assert history[-1]['afterSha256']==sha(before)
 record=dict(type='image-assets',batches=['data/batches/2026-10-25-quality-images.csv'],beforeSha256=sha(before),afterSha256=sha(after),modifiedLines=[dict(id=i,before=b,after=c) for i,(b,c) in enumerate(zip(text.splitlines()[1:],after.decode().splitlines()[1:]),1) if b!=c])
 manifest['assets']=[replacements.get(a['file'],a) for a in manifest['assets']];manifest['lastCorrectedAt']='2026-10-25';coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=read(coveragepath)
 changed={i for e in edits for i in e['ids']}
 for i in changed:
  c=coverage[i-1];r=rows[i-1];assert c['id']==i
  c.update(**{k:r[k] for k in ('reading','word','meaning','image_asset')});c['quality20261025Review']={'date':'2026-10-25','image':'再生成・目視確認・罫線実測検証済み'}
 assert len(edits)==128 and len(replacements)==128
 assert after==before,'Image replacement must preserve dictionary bytes and IDs.'
 summary=dict(images=len(edits),dictionaryRows=len(rows),affectedRows=len(changed),beforeSha256=sha(before),afterSha256=sha(after),edits=edits)
 if args.apply:
  for e in edits:
   production=ROOT/'assets/shiritori'/e['afterFile'];backup=BASE/'before'/e['beforeFile'];backup.parent.mkdir(parents=True,exist_ok=True)
   if backup.exists():assert sha(backup.read_bytes())==e['beforeSha256']
   else:shutil.copyfile(production,backup)
  for e in edits:
   production=ROOT/'assets/shiritori'/e['afterFile'];shutil.copyfile(BASE/'tiles'/e['validatedTile'],production);assert sha(production.read_bytes())==e['afterSha256']
  csvpath.write_bytes(after);dump(mp,manifest);history.append(record);dump(historypath,history);dump(coveragepath,coverage);dump(ledger,{**summary,'manifestAfterSha256':sha(mp.read_bytes())})
 print(json.dumps({k:v for k,v in summary.items() if k!='edits'},ensure_ascii=False))
if __name__=='__main__':main()
