"""Check all vocabulary/images by the same criteria. Missing dictionary entries are review candidates, never proof of invalidity.

python scripts/audit-shiritori-quality.py --dictionary /path/to/JMdict_e.gz
The external dictionary is optional. Keep its download outside the repository.
"""
import argparse, collections, csv, gzip, hashlib, json, re
from pathlib import Path
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dictionary',type=Path)
parser.add_argument('--output',type=Path)
args=parser.parse_args();root=Path(__file__).resolve().parent.parent
rows=list(csv.DictReader((root/'whitelist.csv').open(encoding='utf-8-sig',newline='')))
manifest=json.loads((root/'assets/shiritori/manifest.json').read_text())
ledger=json.loads((root/'data/corrections/2026-10-11-ledger.json').read_text())
coverage=json.loads((root/'data/image-coverage/review-2026-10-10.json').read_text())
assert len(coverage)==len(rows) and all(e['id']==i and all(e[k]==r[k] for k in ['word','reading','meaning','image_asset']) for i,(e,r) in enumerate(zip(coverage,rows),1)),'Refresh coverage identities before auditing.'
origins=[e.get('originalId') for e in coverage];assets={a['file']:a for a in manifest['assets']}
reviewed_images=set(ledger['replacedImages'])
latest=root/'data/corrections/review93-2026-10-11/ledger.json'
if latest.exists():reviewed_images.update(json.loads(latest.read_text())['replacedImages'])
errors=[];candidates=[];resolved=[];groups=collections.defaultdict(list);shared=collections.defaultdict(list)
def hira(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
def norm(s):return re.sub(r'[\s。、「」（）()・]','',hira(s))
dictionary=None;dictionary_meta=None
if args.dictionary:
    content=gzip.open(args.dictionary,'rt',encoding='utf-8').read();dictionary=collections.defaultdict(set)
    for entry in re.findall(r'<entry>(.*?)</entry>',content,re.S):
        readings={hira(x) for x in re.findall(r'<reb>(.*?)</reb>',entry)}
        for word in re.findall(r'<keb>(.*?)</keb>',entry)+re.findall(r'<reb>(.*?)</reb>',entry):dictionary[word].update(readings)
    dictionary_meta={'name':'JMdict','url':'https://ftp.edrdg.org/pub/Nihongo/JMdict_e.gz',
        'sha256':hashlib.sha256(args.dictionary.read_bytes()).hexdigest(),'checkedAt':'2026-10-11'}
for i,row in enumerate(rows,1):
    ident={'id':i,'originalId':origins[i-1] if i<=len(origins) else None,'reading':row['reading'],'word':row['word']}
    if not re.fullmatch('[ぁ-ゖー]+',row['reading']):errors.append({**ident,'type':'invalid-reading'})
    if not row['meaning'] or re.search('[,\r\n]',row['meaning']):errors.append({**ident,'type':'invalid-meaning'})
    if norm(row['meaning']) in {norm(row['word']),norm(row['reading']),norm(row['word']+'のこと'),norm(row['reading']+'のこと')}:
        candidates.append({**ident,'type':'circular-definition','meaning':row['meaning']})
    groups[row['reading']].append((i,row));file=row['image_asset']
    if file:shared[Path(file).name].append(i)
    if dictionary is not None and row['reading'] not in dictionary.get(row['word'],set()):
        candidates.append({**ident,'type':'dictionary-reading-mismatch' if row['word'] in dictionary else 'dictionary-unlisted',
            'dictionaryReadings':sorted(dictionary.get(row['word'],set())),
            'reason':'固有名詞・複合語・略称・別の語義もあり得るため、未収録だけでは削除しない。'})
for reading,uses in groups.items():
    for pos,(i,row) in enumerate(uses):
        for j,other in uses[:pos]:
            if norm(row['meaning'])==norm(other['meaning']):
                candidates.append({'type':'possible-spelling-duplicate','reading':reading,'ids':[j,i],
                    'words':[other['word'],row['word']],'reason':'同音異義語や別語義がないか確認してから統合。'})
for file,ids in shared.items():
    if file not in assets:errors.append({'file':file,'type':'missing-manifest'});continue
    a=assets[file];p=root/'assets/shiritori'/file
    if not p.exists():errors.append({'file':file,'type':'missing-image'});continue
    with Image.open(p) as im:
        im.verify()
    with Image.open(p) as im:
        if im.width!=im.height:errors.append({'file':file,'type':'nonsquare-image'})
        if a.get('generatedAt')=='2026-10-11' and im.size!=(256,256):errors.append({'file':file,'type':'unexpected-size'})
        # A near-white horizontal separator followed by colored content can be an adjacent tile.
        if a.get('sourceSheet') and im.width==256:
            pixels=im.convert('RGB');bands=[]
            for y in range(195,250):
                white=sum(min(pixels.getpixel((x,y)))>=235 for x in range(256))/256
                if white>.97:bands.append(y)
            if any(y+1 in bands and y+2 in bands and sum(min(pixels.getpixel((x,255)))<220 for x in range(256))>40 for y in bands):
                alert={'file':file,'ids':ids,'type':'possible-bottom-fragment','reason':'白い境界の後に絵がある。内容を失わないか確認してから画像を修正。'}
                if file in reviewed_images:
                    alert['resolution']='切り出し後の目視でコマ混入ではなく場面内の余白と確認。';resolved.append(alert)
                else:candidates.append(alert)
    expected={(i,rows[i-1]['reading'],rows[i-1]['word'],rows[i-1]['meaning']) for i in ids}
    actual={(x['id'],x['reading'],x['word'],x['meaning']) for x in a.get('aliases',[])}
    if expected!=actual:errors.append({'file':file,'type':'stale-aliases'})
    if len(ids)>1 and file not in reviewed_images and not a.get('sharedSenseReview',{}).get('reviewed'):
        candidates.append({'file':file,'ids':ids,'type':'shared-senses-review','words':[rows[i-1]['word'] for i in ids],
            'reason':'画像が読めることと全語義が合うことは別。既存の一律reviewed表示を、全語義の目視合格とみなさない。'})
report={'checkedAt':'2026-10-11','vocabularyRows':len(rows),'imagesChecked':len(shared),'structuralErrors':errors,
    'dictionary':dictionary_meta,'candidates':candidates,'resolvedHeuristicAlerts':resolved,'candidateCounts':dict(collections.Counter(c['type'] for c in candidates)),
    'limitations':'全件の構造・辞書照合・重複・共有関係・切り出し境界を自動点検した記録。意味や表情の全件目視合格ではない。未収録や画像の疑いを根拠なく自動削除・切断しない。'}
out=args.output or root/'data/corrections/2026-10-11-quality.json'
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['vocabularyRows','imagesChecked','candidateCounts']},ensure_ascii=False))
if errors:print(json.dumps(errors,ensure_ascii=False));raise SystemExit(1)
