"""Build a resumable, source-backed ordinary-word queue; never import automatically."""
import argparse, collections, csv, hashlib, json, re, subprocess, unicodedata
from pathlib import Path

def norm(t): return unicodedata.normalize('NFKC', t)
def hira(t): return ''.join(chr(ord(c)-96) if 'ァ' <= c <= 'ヶ' else c for c in norm(t))
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def audit(root):
    # Fetch upstream before invoking this tool. A known-behind checkout must not
    # turn already published vocabulary into new-word candidates.
    subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=root,check=True)
    baseline_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    upstream_commit=subprocess.check_output(['git','rev-parse','origin/main'],cwd=root,text=True).strip()
    folder=root/'data/lexical-expansion'
    config=load(folder/'families.json')
    raw=(root/'whitelist.csv').read_bytes()
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    pairs=collections.defaultdict(list)
    for i,r in enumerate(rows): pairs[(hira(r['reading']),norm(r['word']))].append(i+1)
    readings={hira(r['reading']) for r in rows}
    source=root/'data/general10000/sources/jmdict-eng-3.6.2.json'
    jm=load(source)
    blocks=[]
    for line in (root/'blacklist.txt').read_text(encoding='utf-8-sig').splitlines():
        line=line.strip()
        if not line or line.startswith('#'): continue
        m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I)
        blocks.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
    excluded={'arch','obs','rare','vulg','derog','sl','dated','sens','X'}
    unsuitable=re.compile(r'性玩具|枕絵|春画|陰茎|陰嚢|玉袋|膣|性交|自慰|売春|猥褻|麻薬|覚醒剤|\b(?:sex|sexual|erotic|pornography|pornographic|vagina|penis|scrotum|testicle|masturbation|prostitution|suicide)\b',re.I)
    counts=collections.Counter(); inventory={}; queue={}
    for family in config['families']:
        inventory[family['id']]={**family,'sourcePairs':0,'surfacePresent':0,'missingPairs':0,'pendingSemanticReview':0}
    for entry in jm['words']:
        for kana in entry['kana']:
            reading=hira(kana['text'])
            if not re.fullmatch('[ぁ-ゖー]{1,30}',reading) or reading.startswith('ん'): continue
            if any(reading==v if mode=='exact' else v in reading for mode,v in blocks):
                counts['blacklistReading']+=1; continue
            for form in entry['kanji'] or [{'text':kana['text'],'tags':[],'common':kana['common']}]:
                word=form['text']; key=(reading,norm(word))
                if unsuitable.search(word):
                    counts['unsuitableWord']+=1; continue
                if '*' not in kana['appliesToKanji'] and word not in kana['appliesToKanji']: continue
                if any(t in form.get('tags',[]) for t in ['iK','ik','oK','rk','sK']): continue
                if re.search('[,\r\n\t/／()（）]',word): continue
                senses=[]
                for number,sense in enumerate(entry['sense'],1):
                    if not set(sense['partOfSpeech']) & {'n','n-adv','n-t','n-vs'}: continue
                    if sense['dialect'] or set(sense['misc']) & excluded: continue
                    if unsuitable.search(' '.join(g['text'] for g in sense['gloss'])):
                        counts['unsuitableSense']+=1; continue
                    if '*' not in sense['appliesToKana'] and kana['text'] not in sense['appliesToKana']: continue
                    if '*' not in sense['appliesToKanji'] and word not in sense['appliesToKanji']: continue
                    senses.append(number)
                if not senses: continue
                families=[f['id'] for f in config['families'] if any(a in word for a in f['anchors'])]
                common=kana['common'] or form.get('common',False)
                if not families and not common: continue
                present=key in pairs
                if key not in queue:
                    queue[key]=dict(key=reading+'\t'+word,reading=reading,word=word,families=[],common=common,readingCommon=kana['common'],
                        status='surface-present-sense-unchecked' if present else 'pending-review',
                        gap='existing-pair' if present else 'new-spelling-or-sense' if reading in readings else 'new-reading',
                        existingIds=pairs.get(key,[]),endsWithN=reading.endswith('ん'),evidence=[],
                        matchMethod='headword-substring-candidate-only',semanticReview='pending')
                item=queue[key]; item['families']=sorted(set(item['families']+families))
                item['common'] |= common
                item['readingCommon'] |= kana['common']
                item['evidence'].append(dict(entryId=entry['id'],senseNumbers=senses,
                    sourceWord=word,sourceKana=kana['text'],url='https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&seq='+entry['id']))
    ordered=sorted(queue.values(),key=lambda r:(r['status']!='pending-review',not r['readingCommon'],not bool(r['families']),not r['common'],len(r['reading']),r['reading'],r['word']))
    # Editorial decisions live separately and are never replaced by a refreshed audit.
    decisions={}
    for file in sorted(folder.glob('decisions/*.jsonl')):
        for line in file.read_text(encoding='utf-8').splitlines():
            d=json.loads(line); decisions[(d['reading'],norm(d['word']))]=d
    for item in ordered:
        for fid in item['families']:
            inventory[fid]['sourcePairs']+=1
            inventory[fid]['surfacePresent' if item['existingIds'] else 'missingPairs']+=1
            inventory[fid]['pendingSemanticReview']+=1
        d=decisions.get((item['reading'],norm(item['word'])))
        if d: item['editorialDecision']=d['status']; item['decisionId']=d['id']
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'queue.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in ordered),encoding='utf-8')
    save(folder/'family-coverage.json',list(inventory.values()))
    summary=dict(schema=1,baselineCommit=baseline_commit,upstreamCommit=upstream_commit,baselineSha256=hashlib.sha256(raw).hexdigest(),baselineRows=len(rows),
        baselineReadings=len(readings),source=dict(file=source.relative_to(root).as_posix(),sha256=hashlib.sha256(source.read_bytes()).hexdigest(),dictDate=jm['dictDate']),
        families=len(inventory),queuePairs=len(ordered),statuses=dict(collections.Counter(r['status'] for r in ordered)),
        missingFamilyPairs=sum(r['status']=='pending-review' and bool(r['families']) for r in ordered),
        missingCommonPairs=sum(r['status']=='pending-review' and r['common'] for r in ordered),
        decisions=len(decisions),filters=dict(counts),
        limits=['Substring matches propose families; they do not establish semantic membership.',
                'An existing reading and spelling does not prove that all ordinary senses are present.',
                'Source eligibility is not child-suitability review. No automatic adoption.',
                'Coverage is relative to this source and taxonomy; it is not completeness of Japanese.',
                'Frequency data and unknown-input logs are not yet ingested.'])
    save(folder/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args();audit(a.root)
