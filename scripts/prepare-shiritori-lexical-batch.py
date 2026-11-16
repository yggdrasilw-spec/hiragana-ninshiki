"""Prepare and optionally append explicitly edited life/family vocabulary.

Candidate generation cannot adopt a word. Only the editorial TSV is considered.
Use --apply after inspecting the review and the source senses.
"""
import collections, csv, hashlib, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BATCH=sys.argv[sys.argv.index('--batch')+1] if '--batch' in sys.argv else '2026-11-16-life-family'
if BATCH not in {'2026-11-16-life-family','2026-11-16-life-family-02'}:raise ValueError('Unknown editorial batch')
D=ROOT/'data/lexical-expansion'
BASE=ROOT/'data/dictionary-imports'/BATCH
HEADER='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(*args): subprocess.run(args,cwd=ROOT,check=True)

def prepare():
    summaryfile=BASE.with_suffix('.summary.json')
    if summaryfile.exists() and read(summaryfile).get('registered'):
        s=read(summaryfile)
        current={(x['reading'],x['word'],x['meaning']) for x in csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig'))}
        assert all((x['reading'],x['word'],x['meaning']) in current for x in read(BASE.with_suffix('.review.json'))),'Registered batch is incomplete'
        if not s.get('deliveryBuilt'):
            run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
            s['deliveryBuilt']=True;save(summaryfile,s)
        print(json.dumps({'alreadyRegistered':True,'batch':BATCH,'added':s['added']}));return
    raw=(ROOT/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    summary=read(D/'summary.json')
    assert summary['baselineSha256']==sha(raw),'Audit is stale; refresh it first'
    bypair=collections.defaultdict(list);byreading=collections.defaultdict(list)
    for index,x in enumerate(old,1):
        bypair[(x['reading'],x['word'])].append(index);byreading[x['reading']].append(index)
    known_readings=frozenset(byreading)
    queue={}
    for line in (D/'queue.jsonl').read_text(encoding='utf-8').splitlines():
        x=json.loads(line);queue[(x['reading'],x['word'])]=x
    families={x['id']:x for x in read(D/'families.json')['families']}
    families['general']=dict(id='general',scene='日常の言葉・学習・社会',anchors=[])
    seed=list(csv.DictReader((D/'editorial'/f'{BATCH}.tsv').open(encoding='utf-8'),delimiter='\t'))
    assert len({(x['reading'],x['word']) for x in seed})==len(seed),'Duplicate editorial pair'
    reviews=[];skipped=[];held=[];decisions=[];lines=[];entries=[]
    criteria={1:'小学1・2年生の日常場面を想定。',2:'小学3・4年生の生活・活動を想定。',3:'小学5・6年生で扱う仕組みや名称を想定。',4:'専門的・発展的な語義としてレベル4に置く。'}
    different={'こぶくろ':'既存の芸能グループ名「コブクロ」や器官名「子袋」と区別し、小さな袋の普通の意味を補完。',
               'しふく':'既存の「至福」と区別し、制服ではない衣服の意味を補完。',
               'こばこ':'既存の装飾付きの容器「小匣」より広く、小さな箱の一般的な意味と表記を補完。'}
    for x in seed:
        key=(x['reading'],x['word']);decision=dict(id=BATCH+':'+x['reading']+':'+x['word'],**x)
        if key in bypair:
            # Current seed's existing ordinary senses were compared individually.
            skipped.append(dict(**x,existingIds=bypair[key],reason='同じ読み・表記の一般的な意味を既存説明で確認。'))
            decisions.append(dict(**decision,status='existing-ordinary-sense-confirmed'));continue
        candidate=queue.get(key)
        if not candidate:
            held.append(dict(**x,reason='今回の出典照合を通過していない。読み・見出しの独立確認待ち。'))
            decisions.append(dict(**decision,status='hold-source-check'));continue
        assert candidate['status']=='pending-review'
        grade=int(x['grade']);assert grade in criteria and x['family'] in families
        assert x['family']=='general' or x['family'] in candidate['families'],'Family membership needs separate evidence'
        assert not any(c in x['meaning']+x['word'] for c in ',\t\r\n')
        evidence=candidate['evidence'];ids=sorted({e['entryId'] for e in evidence})
        reason=different.get(x['reading'],'同じ意味の別表記を保持する方針で収録。既存の読みを使った既出判定は維持する。') if byreading[x['reading']] else ''
        relation='distinct-ordinary-sense' if x['reading'] in different else 'alternate-spelling' if byreading[x['reading']] else 'new-reading'
        urls=[e['url'] for e in evidence]
        if x['word']=='芋餅': urls.append('https://www.maff.go.jp/j/keikaku/syokubunka/k_ryouri/search_menu/menu/imomochi_hokkaido.html')
        item=dict(id=len(old)+len(reviews)+1,reading=x['reading'],word=x['word'],meaning=x['meaning'],
            level=min(grade,3),grade=grade,category='生活場面・複合語',genre=x['genre'],family=x['family'],scene=families[x['family']]['scene'],
            lexicalSource='JMdict 2026-10-05: '+', '.join(ids),evidence=evidence,sources=list(dict.fromkeys(urls)),
            meaningReason='適用可能な出典の名詞語義と今回の説明を個別に照合し、生活場面に合う短い日本語で独自編集。'+('じゃがいもを用いる北海道の意味は農林水産省資料で補足確認。' if x['word']=='芋餅' else ''),
            ageReason=criteria[grade]+families[x['family']]['scene']+'の「'+x['word']+'」として語義別に編集判断。公的な学年認定ではない。',
            distinctSenseReason=reason,relation=relation,existingSameReadingIds=byreading[x['reading']],
            imageReason='今回の語彙追加は説明カード。一般物の画像補完候補として保持する。',
            imageEligible=True,image_asset='',image_mode='none',definitionAuthor='独自作成',reviewStatus='editorially-reviewed')
        reviews.append(item)
        source=dict(title='JMdict / EDRDG（読み・見出し）・独自説明',url=urls[0],license='CC BY-SA 4.0',verification='applicable-noun-sense-and-editorial-review',jmdictIds=ids)
        if x['word']=='芋餅':source.update(title='農林水産省・うちの郷土料理 / JMdict（読み・見出し）',url=urls[-1])
        entries.append(dict(reading=x['reading'],word=x['word'],meaning=x['meaning'],genre=x['genre'],source=source))
        lines.append(','.join([x['reading'],x['word'],x['meaning'],'',str(min(grade,3)),'','','none','']))
        decisions.append(dict(**decision,status='approved',relation=relation,reviewId=item['id']))
    (BASE.with_suffix('.csv')).write_text(HEADER+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    save(BASE.with_suffix('.review.json'),reviews);save(BASE.with_suffix('.entries.json'),entries)
    save(BASE.with_suffix('.existing.json'),skipped);save(BASE.with_suffix('.held.json'),held)
    decisionpath=D/'decisions'/f'{BATCH}.jsonl';decisionpath.parent.mkdir(parents=True,exist_ok=True)
    decisionpath.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in decisions),encoding='utf-8')
    s=dict(batch=BATCH,registered=False,baselineRows=len(old),baselineSha256=sha(raw),editorialCandidates=len(seed),
        added=len(reviews),newReadings=len({x['reading'] for x in reviews}-known_readings),
        existingReadings=len({x['reading'] for x in reviews}&known_readings),skippedExisting=len(skipped),held=len(held),
        familyCounts=dict(collections.Counter(x['family'] for x in reviews)),gradeCounts=dict(collections.Counter(x['grade'] for x in reviews)),
        endsWithN=sum(x['reading'].endswith('ん') for x in reviews),sourceDate=summary['source']['dictDate'],
        sourceSha256=summary['source']['sha256'],imagesGenerated=0)
    save(summaryfile,s)
    run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append','--validate-only')
    if '--apply' not in sys.argv:
        print(json.dumps(s,ensure_ascii=False));return
    dfile=ROOT/'data/shiritori-grade-decisions.json';d=read(dfile)
    assert d['sourceSha256']==sha(raw) and d['reviewedRows']==len(old)
    assert read(ROOT/'data/dictionary-imports/history.json')[-1]['afterSha256']==sha(raw)
    assert (ROOT/'whitelist.csv').read_bytes()==raw,'Concurrent dictionary edit'
    run('node','scripts/import-shiritori-words.cjs',str(BASE.with_suffix('.csv')),'--append')
    after=(ROOT/'whitelist.csv').read_bytes();assert after.startswith(raw)
    assert len(after.splitlines())-1==len(old)+len(reviews)
    for x in reviews:
        d['levels'][str(x['grade'])]+=' '+str(x['id']-1)
        d.setdefault('notes',{})[str(x['id']-1)]=x['ageReason']
    d.update(sourceSha256=sha(after),reviewedRows=len(old)+len(reviews));save(dfile,d)
    # Existing global image ledgers stop before earlier batches. Do not relabel
    # their coverage; new items explicitly retain their own pending image status.
    s.update(registered=True,afterSha256=sha(after),totalRows=len(old)+len(reviews))
    save(summaryfile,s)
    run(sys.executable,'-B','-X','utf8','scripts/build-shiritori-grade-bands.py')
    s['deliveryBuilt']=True;save(summaryfile,s)
    print(json.dumps(s,ensure_ascii=False))

if __name__=='__main__':prepare()
