"""Prepare reviewed assets, then import only after R2 readback verification."""
import argparse,collections,csv,hashlib,importlib.util,json,mimetypes,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-19-request25';NAME=OUT.name
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
run=lambda *args:subprocess.run(args,cwd=ROOT,check=True)
p=argparse.ArgumentParser();p.add_argument('--import-reviewed',action='store_true');a=p.parse_args()
plan=json.loads((OUT/'plan.json').read_text(encoding='utf-8'));items=plan['items']
assert sha((ROOT/'whitelist.csv').read_bytes())==plan['baselineSha256'],'Concurrent dictionary change; rebase required'
spec=importlib.util.spec_from_file_location('grid',ROOT/'scripts/crop-shiritori-grid.py');grid=importlib.util.module_from_spec(spec);spec.loader.exec_module(grid)
sources={
 'history':dict(title='Constantinople through the Ages - Utrecht University',url='https://research-portal.uu.nl/ws/files/248229747/9789004710986-BP000017.pdf'),
 'reptile':dict(title='Natural History Museum: What is a plesiosaur?',url='https://www.nhm.ac.uk/discover/what-is-a-plesiosaur.html'),
 'umlaut':dict(title='Goethe-Institut: German Umlaut',url='https://www.goethe.de/resources/files/pdf333/cd_cultural-exploration-german-primary-worksheets.pdf'),
 'glico':dict(title='江崎グリコ: 栄養菓子グリコ',url='https://www.glico.com/assets/files/NR20221202.pdf'),
 'puma':dict(title='PUMA公式 会社概要',url='https://jp.puma.com/jp/ja/help/about-us'),
 'anthem':dict(title='内閣府 国旗・国歌について',url='https://www8.cao.go.jp/chosei/kokkikokka/kokkikokka'),
 'frog':dict(title='環境省 特定外来生物 ウシガエル',url='https://www.env.go.jp/nature/intro/4document/files/r_bullfrog_shikoku.pdf'),
 'telework':dict(title='厚生労働省 テレワークとは',url='https://telework.mhlw.go.jp/telework/about/'),
 'plum':dict(title='Kew Prunus domestica',url='https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:30221374-2/general-information')}
source_by_word={'コンスタンティノープル':'history','ビザンツ':'history','エラスモサウルス':'reptile','首長竜':'reptile','ウムラウト':'umlaut','グリコ':'glico','君が代':'anthem','国歌':'anthem','ウシガエル':'frog','テレワーク':'telework','リモートワーク':'telework','プルーン':'plum'}
review=[]
for n in range(1,5):
 suffix='-v2' if n==2 else '';report=OUT/f'sheet{n:02}{suffix}-crop.json';source=ROOT/'assets/shiritori/sheets'/f'request25-sheet{n:02}{suffix}.png'
 grid.verify_report(report,source,ROOT/'assets/shiritori')
 group=[x for x in items if x.get('sheet')==n]
 for x in group:
  if n==2:x['filename']=x['filename'].replace('request25-','request25v2-')
  x.update(sourceSheet=source.relative_to(ROOT/'assets/shiritori').as_posix(),cropValidation=report.relative_to(ROOT).as_posix(),prompt=source.with_suffix('.prompt.txt').read_text(encoding='utf-8'))
 review.append(dict(sourceSheet=source.relative_to(ROOT/'assets/shiritori').as_posix(),passed=True,approvedSlots=[x['tileIndex'] for x in group],notes={1:'めんこの札・ウシガエルの鼓膜・めっき断面・4ひれの首長竜・歌う場面を確認。歴史都市は復元イメージ。',2:'ベーゴマを軸のない金属こまへ修正。ミンク・プーマ・獅子舞・狛犬・カジカガエルなどを語義と照合。',3:'銀めっき・トタン・プルーン・粘性比較・通信場面・白と茶色のソースを照合。歴史都市は復元イメージ。',4:'子房と胚珠・小石・4ひれのエラスモサウルス・イタチ・テン・獅子頭・神楽を照合。余り3コマは未登録。'}[n]))
def centered(d,xy,text,size,maxwidth=680):
 font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',size)
 while d.textbbox((0,0),text,font=font)[2]>maxwidth:
  size-=1;font=ImageFont.truetype('C:/Windows/Fonts/meiryo.ttc',size)
 d.text(xy,text,font=font,fill='#233c50',anchor='mm')
for x in items:
 if x['word'] in source_by_word:x['lexicalSource']['primaryReference']=sources[source_by_word[x['word']]]
 if x['word']=='プーマ' and x['grade']==5:x['lexicalSource']['primaryReference']=sources['puma']
 if x['word']=='粘り強さ':x['lexicalSource']['derivation']='粘り強い（形容詞）の程度・性質を表す名詞形。語幹に「さ」をつける一般的な名詞化。'
 if x['word']=='脂肪分':x['lexicalSource']['derivation']='JMdict 脂肪（1311820）＋成分の「分」。食品に含まれる脂肪を指す複合名詞。'
 assert x['lexicalSource'].get('entries') or x['lexicalSource'].get('primaryReference') or x['lexicalSource'].get('derivation'),x['word']
 if x['credit']=='AI生成イラスト':continue
 im=Image.new('RGB',(768,768),'#fffdf7');d=ImageDraw.Draw(im)
 d.rounded_rectangle((20,20,748,748),radius=35,outline='#cbdce5',width=5)
 centered(d,(384,115),x['word'],56)
 if x['word']=='ウムラウト':
  centered(d,(384,290),'a   o   u',102);centered(d,(384,410),'↓   ↓   ↓',72);centered(d,(384,535),'ä   ö   ü',108)
  centered(d,(384,660),'字の上に 二つの点',35)
 else:
  centered(d,(384,330),'PUMA' if x['word']=='プーマ' else 'グリコ',105)
  centered(d,(384,460),'スポーツの ブランド' if x['word']=='プーマ' else 'キャラメル菓子の 商品名',38)
  centered(d,(384,620),x['reading'],43)
 src=ROOT/'assets/shiritori/sheets'/f'request25-diagram-word-{x["id"]}.png'
 im.save(src);im.resize((256,256),Image.Resampling.LANCZOS).save(ROOT/'assets/shiritori'/x['filename'])
 x.update(sourceSheet=src.relative_to(ROOT/'assets/shiritori').as_posix(),tileIndex=1,cropValidation='',prompt='Reproducible Pillow diagram/card from scripts/finalize-shiritori-request25.py; official logos and product packaging are not reproduced.')
 x['imageReason']='ウムラウトの3字と二つの点を正しく描画。' if x['word']=='ウムラウト' else '商品・ブランド名を一般書体で示す独自文字カード。公式ロゴや商品画像ではない。外部検索をしない。'
save(OUT/'semantic-review.json',review);save(OUT/'sources.json',sources)
save(OUT/'plan.json',plan)
paths={ROOT/'assets/shiritori'/x['filename'] for x in items}
paths.update((ROOT/'assets/shiritori/sheets').glob('request25-*.png'))
# Rejected original sheet-2 crops remain archived locally and are never referenced.
entries=[dict(key=f.relative_to(ROOT).as_posix(),bucket='shiritori-images' if f.parent==ROOT/'assets/shiritori' else 'shiritori-image-archive',bytes=f.stat().st_size,sha256=sha(f.read_bytes()),contentType=mimetypes.guess_type(f.name)[0]) for f in sorted(paths)]
save(OUT/'r2-upload.json',dict(batch=NAME,entries=entries))
if not a.import_reviewed:
 print(json.dumps(dict(prepared=True,publicImages=64,objects=len(entries))));sys.exit()
journal=ROOT/'qa-output/request25-r2-transfer.jsonl'
verified={x['bucket']+'/'+x['key']:x['sha256'] for x in (json.loads(l) for l in journal.read_text(encoding='utf-8').splitlines()) if x.get('verified')}
assert all(verified.get(e['bucket']+'/'+e['key'])==e['sha256'] for e in entries),'Upload and readback required before dictionary import'
decisions_path=ROOT/'data/shiritori-grade-decisions.json';decisions=json.loads(decisions_path.read_text(encoding='utf-8'))
assert decisions['sourceSha256']==plan['baselineSha256']
batch=ROOT/'data/dictionary-imports'/(NAME+'.csv')
with batch.open('w',encoding='utf-8',newline='') as f:
 w=csv.writer(f,lineterminator='\n');w.writerow('reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'.split(','))
 for x in items:w.writerow([x['reading'],x['word'],x['meaning'],x['word'],x['level'],'','','',''])
save(batch.with_suffix('.review.json'),items)
columns='id,reading,word,meaning,filename,scene,sourceSheet,tileIndex,generatedAt,prompt,cropValidation,credit'.split(',')
imagebatch=ROOT/'data/batches'/(NAME+'-images.csv')
with imagebatch.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for x in items:w.writerow({k:'2026-10-19' if k=='generatedAt' else x[k] for k in columns})
run('node','scripts/import-shiritori-words.cjs',str(batch),'--append','--validate-only');run('node','scripts/import-shiritori-words.cjs',str(batch),'--append')
run(sys.executable,'-X','utf8','scripts/import-shiritori-assets.py',str(imagebatch))
after=(ROOT/'whitelist.csv').read_bytes();base=(OUT/'registration-baseline.csv').read_bytes();assert after.startswith(base)
rows=list(csv.DictReader(after.decode('utf-8').splitlines()))
for level in range(1,6):
 ids=[x['id']-1 for x in items if x['grade']==level]
 if ids:decisions['levels'][str(level)]+=' '+' '.join(map(str,ids))
for x in items:decisions.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
decisions.update(sourceSha256=sha(after),reviewedRows=len(rows));save(decisions_path,decisions)
run(sys.executable,'-X','utf8','scripts/build-shiritori-grade-bands.py')
coveragepath=ROOT/'data/image-coverage/review-2026-10-10.json';coverage=json.loads(coveragepath.read_text(encoding='utf-8'));assert len(coverage)==plan['baselineRows']
for x in items:
 r=rows[x['id']-1];coverage.append(dict(id=x['id'],**{k:r[k] for k in ('reading','word','meaning','level','image_asset')},category='requested-vocabulary',target=True,scopeReason='指定25語と周辺語・同音異義語を追加。',status='covered',assignment='new',originalId=None))
save(coveragepath,coverage)
summary=dict(date='2026-10-19',requestedReadings=25,addedMeanings=len(items),newReadings=len({x['reading'] for x in items}-{r['reading'] for r in csv.DictReader(base.decode('utf-8').splitlines())}),rows=len(rows),generatedIllustrations=61,diagrams=1,nameCards=2,missingImages=0,r2VerifiedObjects=len(entries),beforeSha256=sha(base),afterSha256=sha(after),grades=dict(collections.Counter(x['grade'] for x in items)))
save(OUT/'summary.json',summary);save(batch.with_suffix('.summary.json'),summary)
run(sys.executable,'-X','utf8','scripts/build-shiritori-review-updates.py')
print(json.dumps(summary,ensure_ascii=False))
