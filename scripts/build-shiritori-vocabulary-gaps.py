"""Reproducible discovery ledger. Evidence is a candidate, never approval."""
import argparse, collections, csv, datetime, hashlib, io, json, re, sqlite3
import subprocess, unicodedata, zipfile
from pathlib import Path
from shiritori_lexical_policy import REJECT_MISC

def norm(s): return unicodedata.normalize('NFKC', s).strip()
def hira(s): return ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in norm(s))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, obj): p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def applies(values, text): return '*' in values or text in values

def eligible_senses(entry, kana, form):
    if 'ok' in kana.get('tags', []) or set(form.get('tags', [])) & {'iK','ik','sK'}:
        return []
    if not applies(kana['appliesToKanji'], form['text']): return []
    return [dict(number=i, gloss=[g['text'] for g in s['gloss']], pos=s['partOfSpeech'],
                 misc=s['misc'], dialect=s['dialect'])
            for i,s in enumerate(entry['sense'], 1)
            if set(s['partOfSpeech']) & {'n','n-adv','n-t','n-vs'}
            and not set(s['misc']) & REJECT_MISC
            and applies(s['appliesToKana'], kana['text'])
            and applies(s['appliesToKanji'], form['text'])]

def build(root, jmdict, resume=False):
    out=root/'data/vocabulary-gap'; out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=root,check=True)
    raw=(root/'whitelist.csv').read_bytes()
    rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    pairs=collections.defaultdict(list)
    for i,r in enumerate(rows,1): pairs[(hira(r['reading']),norm(r['word']))].append(i)
    readings={k[0] for k in pairs}
    families=json.loads((root/'data/lexical-expansion/families.json').read_text(encoding='utf-8'))['families']
    rules=[]
    for line in (root/'blacklist.txt').read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if line and not line.startswith('#'):
            m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I)
            rules.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
    db=sqlite3.connect(out/'candidates.sqlite3')
    if not resume:
        db.executescript('''DROP TABLE IF EXISTS evidence; DROP TABLE IF EXISTS candidates;
          CREATE TABLE candidates(reading TEXT, word TEXT, commonReading INT DEFAULT 0,
            commonForm INT DEFAULT 0, jmdict INT DEFAULT 0, sudachi INT DEFAULT 0,
            families TEXT, existingIds TEXT, gap TEXT, endsWithN INT, PRIMARY KEY(reading,word));
          CREATE TABLE evidence(reading TEXT, word TEXT, source TEXT, location TEXT, details TEXT,
            PRIMARY KEY(reading,word,source,location));''')
    counters=collections.Counter(); source_meta=[]
    def add(reading, word, source, location, details, common_reading=False, common_form=False):
        reading=hira(reading); word=norm(word)
        if not re.fullmatch('[ぁ-ゖー]{1,120}',reading) or not word or re.search('[,\r\n\t<>]',word):
            counters[source+':unsupported-form']+=1; return
        # Mark potential content risks for review rather than treating an untagged source as safe.
        if any(reading==v if mode=='exact' else v in reading for mode,v in rules):
            counters[source+':blacklist']+=1; return
        key=(reading,word); present=key in pairs
        gap='existing-pair-sense-audit' if present else 'same-reading-new-surface' if reading in readings else 'new-reading'
        fs=[f['id'] for f in families if any(a in word for a in f['anchors'])]
        db.execute('''INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(reading,word) DO UPDATE SET
          commonReading=MAX(commonReading,excluded.commonReading), commonForm=MAX(commonForm,excluded.commonForm),
          jmdict=MAX(jmdict,excluded.jmdict),sudachi=MAX(sudachi,excluded.sudachi)''',
          (reading,word,int(common_reading),int(common_form),int(source=='jmdict'),int(source.startswith('sudachi')),
           json.dumps(fs,ensure_ascii=False),json.dumps(pairs.get(key,[])),gap,int(reading.endswith('ん'))))
        db.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?)',
                   (reading,word,source,str(location),json.dumps(details,ensure_ascii=False,separators=(',',':'))))
    if resume:
        checkpoint=json.loads((out/'index-checkpoint.json').read_text(encoding='utf-8'))
        assert checkpoint['baselineSha256']==hashlib.sha256(raw).hexdigest(), 'Changed baseline; rebuild required'
        assert checkpoint['jmdictSha256']==digest(jmdict), 'Changed JMdict; rebuild required'
        source_meta=checkpoint['sources'];counters.update(checkpoint['filters'])
        for source in source_meta:
            if source['id'].startswith('sudachi'):
                assert digest(out/'sources'/source['file'])==source['sha256'], 'Changed Sudachi; rebuild required'
    else:
        jm=json.loads(jmdict.read_text(encoding='utf-8'))
        source_meta.append(dict(id='jmdict',file=jmdict.name,sha256=digest(jmdict),date=jm['dictDate'],
            url='https://www.edrdg.org/jmdict/j_jmdict.html',license='CC BY-SA 4.0',
            retrieval='Existing frozen source; see data/general10000/source-metadata.json'))
        for e in jm['words']:
            for k in e['kana']:
                for f in e['kanji'] or [dict(text=k['text'],tags=[],common=k['common'])]:
                    senses=eligible_senses(e,k,f)
                    if not senses: continue
                    add(k['text'],f['text'],'jmdict',e['id'],dict(entryId=e['id'],kana=k['text'],word=f['text'],
                        kanaTags=k.get('tags',[]),formTags=f.get('tags',[]),senses=senses,
                        url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&seq='+str(e['id'])),k['common'],f.get('common',False))
        del jm
        db.commit(); print('JMdict indexed',flush=True)
        for edition in ['small','core']:
            path=out/'sources'/f'{edition}_lex.zip'; source='sudachi-'+edition
            source_meta.append(dict(id=source,file=path.name,sha256=digest(path),date='20261015',
              url=f'https://sudachi.s3.ap-northeast-1.amazonaws.com/sudachidict-raw/v1/20261015/{edition}_lex.zip',
              license='Apache-2.0 and bundled notices; see SudachiDict-LEGAL'))
            with zipfile.ZipFile(path) as z, z.open(edition+'_lex.csv') as stream:
                for line,r in enumerate(csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8')),2):
                    counters[source+':raw-rows']+=1
                    if r['POS1']!='名詞' or r['POS2']!='普通名詞':
                        counters[source+':outside-ordinary-noun-scope']+=1; continue
                    # V1 Headword can be empty. IndexForm is an attested spelling;
                    # NormalizedForm contains a structured reference, not a display word.
                    word=r['Headword'] or r['IndexForm']
                    add(r['ReadingForm'],word,source,line,dict(member=edition+'_lex.csv',line=line,
                        indexForm=r['IndexForm'],headword=r['Headword'],readingForm=r['ReadingForm'],
                        normalizedReference=r['NormalizedForm'],pos=[r[f'POS{i}'] for i in range(1,7)],
                        interpretation='Reading/form evidence only; no definition or suitability proof.'))
            db.commit(); print(source+' indexed',flush=True)
        dump(out/'index-checkpoint.json',dict(baselineSha256=hashlib.sha256(raw).hexdigest(),
             jmdictSha256=digest(jmdict),sources=source_meta,filters=dict(counters)))
    db.executescript('CREATE INDEX IF NOT EXISTS evidence_pair ON evidence(reading,word); CREATE INDEX IF NOT EXISTS evidence_location ON evidence(source,location);')
    # Same entry only suggests an alias/sense relation. Never count it as a reviewed synonym.
    db.execute('''CREATE TEMP TABLE represented_entries AS SELECT DISTINCT e.location
      FROM evidence e JOIN candidates c USING(reading,word)
      WHERE e.source='jmdict' AND c.gap='existing-pair-sense-audit' ''')
    db.execute('CREATE INDEX represented_locations ON represented_entries(location)')
    print('Source entry links indexed',flush=True)
    linked={(r,w) for r,w in db.execute('''SELECT DISTINCT e.reading,e.word FROM evidence e
      JOIN represented_entries x USING(location) WHERE e.source='jmdict' ''')}
    summary=dict(schema=1,createdAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        baselineCommit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        upstreamCommit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=root,text=True).strip(),
        baselineSha256=hashlib.sha256(raw).hexdigest(),baselineRows=len(rows),baselineReadings=len(readings),
        sources=source_meta,filters=dict(counters),adopted=0)
    counts=collections.Counter(); unique_new=set(); source_counts=collections.Counter(); shortlist=[]
    query='''SELECT * FROM candidates ORDER BY gap='existing-pair-sense-audit',
      endsWithN,commonReading DESC,(jmdict+sudachi) DESC,(families!='[]') DESC,
      commonForm DESC,LENGTH(reading),reading,word'''
    columns=[d[0] for d in db.execute('SELECT * FROM candidates LIMIT 0').description]
    with (out/'queue.jsonl').open('w',encoding='utf-8') as export:
        for values in db.execute(query):
            item=dict(zip(columns,values)); item['families']=json.loads(item['families']);item['existingIds']=json.loads(item['existingIds'])
            item['reviewStatus']='pending';item['relation']='unresolved'
            if item['gap']=='existing-pair-sense-audit':item['relation']='sense-coverage-unchecked'
            elif (item['reading'],item['word']) in linked:item['relation']='same-source-entry-alias-or-sense-review'
            item['evidenceLocations']=[dict(source=s,location=l) for s,l in db.execute('SELECT source,location FROM evidence WHERE reading=? AND word=?',(item['reading'],item['word']))]
            counts[item['gap']]+=1
            if item['gap']=='new-reading':unique_new.add(item['reading'])
            if item['gap']!='existing-pair-sense-audit':
                source_counts['both' if item['jmdict'] and item['sudachi'] else 'jmdict-only' if item['jmdict'] else 'sudachi-only']+=1
                if len(shortlist)<2000:shortlist.append(item)
            export.write(json.dumps(item,ensure_ascii=False,separators=(',',':'))+'\n')
    summary.update(candidatePairs=sum(counts.values()),gaps=dict(counts),missingPairs=sum(v for k,v in counts.items() if k!='existing-pair-sense-audit'),
        uniqueNewReadings=len(unique_new),missingBySource=dict(source_counts),shortlistPairs=len(shortlist),
        limits=['Pending candidates, not approved entries. No dictionary mutation.',
          'Existing reading/form is not proof of meaning coverage; alias/sense classifications require editorial review.',
          'Common markers and family substrings rank candidates; they do not prove frequency, meaning or child suitability.',
          'Sudachi small/core ordinary nouns only. Full proper-name expansion and standalone latest UniDic not ingested.',
          'Sudachi small incorporates part of UniDic; this is not three independent dictionary confirmations.',
          'Ending-n entries are retained and marked; raw reading forms may require pronunciation/old-kana review.',
          'Untagged inappropriate content can remain. Candidate files must not feed CPU/hints directly.'])
    dump(out/'summary.json',summary)
    with (out/'review-first-2000.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['reading','word','gap','relation','commonReading','sources','families','reviewStatus'])
        for r in shortlist:writer.writerow([r['reading'],r['word'],r['gap'],r['relation'],r['commonReading'],
          '|'.join(sorted({x['source'] for x in r['evidenceLocations']})),'|'.join(r['families']),r['reviewStatus']])
    dump(out/'checkpoint.json',dict(phase='inventory-complete',baselineSha256=summary['baselineSha256'],
         next='Review common new readings and source-linked aliases; write decisions separately before any import.',
         completedSources=[x['id'] for x in source_meta],pendingSources=['standalone-latest-UniDic','unknown-input-log'],
         decisionsPath='data/vocabulary-gap/decisions.jsonl'))
    db.commit();db.close();print(json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--jmdict',type=Path,required=True);parser.add_argument('--resume-index',action='store_true')
    a=parser.parse_args();build(a.root,a.jmdict,a.resume_index)
