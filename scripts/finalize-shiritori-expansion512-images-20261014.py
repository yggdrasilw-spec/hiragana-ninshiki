"""Process inspected sheets and register the complete reviewed image batch."""
import argparse,csv,json,shutil,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
NAME='2026-10-14-expansion512-images'
DIR=ROOT/'data/image-coverage'/NAME
parser=argparse.ArgumentParser()
parser.add_argument('--sources',type=Path)
parser.add_argument('--finalize',action='store_true')
parser.add_argument('--version-sheets',help='Comma-separated sheet numbers to save as corrected sibling versions.')
parser.add_argument('--version',default='v2')
args=parser.parse_args()
plan=json.loads((DIR/'plan.json').read_text(encoding='utf-8'))
if args.version_sheets:
    numbers={int(n) for n in args.version_sheets.split(',')}
    for x in plan['items']:
        if x['sheet'] in numbers:
            x['filename']=f'expansion512-oct14-{args.version}-word-{x["id"]}.png'
            x['sourceSheet']=f'sheets/expansion512-oct14-sheet{x["sheet"]:02}-{args.version}.png'
            x['cropValidation']=f'data/image-coverage/{NAME}/sheet{x["sheet"]:02}-{args.version}-crop.json'
    (DIR/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if args.sources:
    sources=json.loads(args.sources.read_text(encoding='utf-8'))
    for number,source in sources.items():
        number=int(number);items=[x for x in plan['items'] if x['sheet']==number]
        assert len(items)==16
        dest=ROOT/'assets/shiritori'/items[0]['sourceSheet']
        assert not dest.exists() or dest.read_bytes()==Path(source).read_bytes(),'Refuse to replace a saved sheet.'
        if not dest.exists():shutil.copyfile(source,dest)
        report=ROOT/items[0]['cropValidation']
        command=[sys.executable,str(ROOT/'scripts/crop-shiritori-grid.py'),str(dest),'--names',','.join(x['filename'][:-4] for x in items),
            '--output',str(ROOT/'assets/shiritori'),'--report',str(report)]
        if report.exists():command.append('--verify-existing')
        result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8')
        print(json.dumps({'sheet':number,'passed':result.returncode==0,'message':result.stdout+result.stderr},ensure_ascii=False))
if args.finalize:
    semantic=json.loads((DIR/'semantic-review.json').read_text(encoding='utf-8'))
    assert len(semantic)==32 and all(s['passed'] and s['notes'] for s in semantic)
    for n in range(1,33):
        items=[x for x in plan['items'] if x['sheet']==n]
        assert any(s['sheet']==n and s['passed'] for s in semantic)
        assert (ROOT/items[0]['cropValidation']).is_file(),n
    live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
    assert len(live)==plan['baselineRows']
    for x in plan['items']:
        r=live[x['id']-1]
        assert all(r[k]==x[k] for k in ('reading','word','meaning'))
        assert int(r['level'])==x['level']
        assert not r['image_asset'] or r['image_asset']=='assets/shiritori/'+x['filename']
    columns=['id','reading','word','meaning','filename','scene','sourceSheet','tileIndex','generatedAt','prompt','cropValidation','credit']
    batch=ROOT/'data/batches'/f'{NAME}.csv'
    with batch.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
        for x in plan['items']:w.writerow({k:(plan['date'] if k=='generatedAt' else x.get(k,'AI生成イラスト' if k=='credit' else '')) for k in columns})
    # Existing importer validates and recomputes every sheet before mutation.
    subprocess.run([sys.executable,str(ROOT/'scripts/import-shiritori-assets.py'),str(batch)],check=True)
    live=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8')))
    coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json'
    coverage=json.loads(coveragepath.read_text(encoding='utf-8'))
    reviews_path=ROOT/'data/dictionary-imports/2026-10-14-expansion512.review.json'
    reviews=json.loads(reviews_path.read_text(encoding='utf-8'))
    byreading={x['reading']:x for x in reviews}
    for x in plan['items']:
        row=live[x['id']-1];entry=coverage[x['id']-1]
        assert all(row[k]==entry[k] for k in ('word','reading','meaning'))
        entry.update(image_asset=row['image_asset'],status='covered',assignment='new',
            scopeReason='2026-10-14追加語の専用画像。語義と場面を目視確認し、罫線を実測・再計算して登録。')
        byreading[x['reading']].update(imageStatus='covered',filename=x['filename'],sourceSheet=x['sourceSheet'],cropValidation=x['cropValidation'],
            imageReason=x['scene'] if x.get('credit')=='プログラム生成図' else '今回の説明の動作・物・性質を示す具体例。抽象語は一例の場面であり、絵だけで定義全体を示すものではない。')
    coveragepath.write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    reviews_path.write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary=dict(addedImages=len(plan['items']),coveredWords=len(plan['items']),remaining=sum(not live[x['id']-1]['image_asset'] for x in plan['items']),
        allIds=[x['id'] for x in plan['items']],sheets=32,baselineSha256=plan['baselineSha256'],afterSha256=hashlib.sha256((ROOT/'whitelist.csv').read_bytes()).hexdigest())
    (DIR/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    subprocess.run([sys.executable,str(ROOT/'scripts/build-shiritori-review-updates.py')],check=True)
    print(json.dumps(summary,ensure_ascii=False))
