"""Regression: image imports preserve existing raw quote-bearing meanings."""
import csv,hashlib,json,subprocess,sys,tempfile,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='shiritori-image-quotes-') as tmp:
 r=Path(tmp)
 for folder in ['scripts','assets/shiritori/sheets','data/corrections','data/dictionary-imports']:(r/folder).mkdir(parents=True,exist_ok=True)
 for p in (ROOT/'scripts').glob('crop-shiritori-grid*.py'):shutil.copy2(p,r/'scripts'/p.name)
 for name in ('import-shiritori-assets.py','shiritori_manifest.py'):shutil.copy2(ROOT/'scripts'/name,r/'scripts'/name)
 original='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit\nえどうぃ,エドウィ,王/"端麗王"。959年没。,エドウィ,3,,,,\nすーぷ,スープ,野菜などを煮た汁の料理。,スープ,1,,,,\n'
 (r/'whitelist.csv').write_text(original,encoding='utf-8',newline='\n')
 (r/'assets/shiritori/manifest.json').write_text('{"assets":[]}',encoding='utf-8')
 (r/'data/corrections/2026-10-11-ledger.json').write_text(json.dumps({'currentOriginalIds':[1,2],'afterSha256':hashlib.sha256(original.encode()).hexdigest()}),encoding='utf-8')
 (r/'data/dictionary-imports/history.json').write_text('[]',encoding='utf-8')
 for p in ['assets/shiritori/test-word-2.png','assets/shiritori/sheets/diagram-test.png']:Image.new('RGB',(256,256),'white').save(r/p)
 with (r/'batch.csv').open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','credit']);writer.writeheader();writer.writerow(dict(id=2,reading='すーぷ',word='スープ',meaning='野菜などを煮た汁の料理。',filename='test-word-2.png',scene='Fixture only',sourceSheet='sheets/diagram-test.png',tileIndex=1,generatedAt='2026-11-01',credit='プログラム生成図'))
 subprocess.run([sys.executable,str(r/'scripts/import-shiritori-assets.py'),str(r/'batch.csv')],check=True,capture_output=True)
 sys.path.insert(0,str(ROOT/'scripts'))
 from shiritori_manifest import read_manifest
 index_path=r/'assets/shiritori/manifest.json'
 index=json.loads(index_path.read_text(encoding='utf-8'))
 assert index['manifestVersion']==2
 asset,=read_manifest(index_path)['assets']
 assert asset['file']=='test-word-2.png' and 'Fixture only' in asset['prompt']
 split_files=[index_path,*sorted((index_path.parent/'manifest-data').glob('*.json'))]
 before_retry=[p.read_bytes() for p in split_files]
 subprocess.run([sys.executable,str(r/'scripts/import-shiritori-assets.py'),str(r/'batch.csv')],check=True,capture_output=True)
 assert before_retry==[p.read_bytes() for p in split_files]
 actual=(r/'whitelist.csv').read_text(encoding='utf-8');assert actual.splitlines()[1]==original.splitlines()[1]
 assert actual.splitlines()[2].rsplit(',',3)[0]==original.splitlines()[2].rsplit(',',3)[0]
 history=json.loads((r/'data/dictionary-imports/history.json').read_text(encoding='utf-8'))
 assert [x['id'] for x in history[-1]['modifiedLines']]==[2]
 assert history[-1]['beforeSha256']==hashlib.sha256(original.encode()).hexdigest()
print('PASS: embedded quotes and all non-image fields survive image import unchanged')
