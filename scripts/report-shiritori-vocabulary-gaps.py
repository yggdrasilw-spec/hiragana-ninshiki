"""Create human-sized review queues and an auditable Japanese report."""
import collections, csv, hashlib, json, sqlite3
from pathlib import Path

root=Path(__file__).resolve().parents[1];out=root/'data/vocabulary-gap'
summary=json.loads((out/'summary.json').read_text(encoding='utf-8'))
db=sqlite3.connect('file:'+str(out/'candidates.sqlite3')+'?mode=ro',uri=True)
assert hashlib.sha256((root/'whitelist.csv').read_bytes()).hexdigest()==summary['baselineSha256']
seen=set();review=[];aliases=[];existing=[];counts=collections.Counter();new_usable=set();new_common=set()
with (out/'queue.jsonl').open(encoding='utf-8') as stream:
    for line in stream:
        r=json.loads(line);counts[r['gap']]+=1
        if r['gap']=='new-reading':
            if not r['endsWithN']:new_usable.add(r['reading'])
            if r['commonReading']:new_common.add(r['reading'])
            if r['reading'] not in seen and not r['endsWithN'] and len(review)<2000:
                review.append(r);seen.add(r['reading'])
        elif r['gap']=='same-reading-new-surface' and len(aliases)<1000:aliases.append(r)
        elif r['gap']=='existing-pair-sense-audit' and len(existing)<500:existing.append(r)
assert sum(counts.values())==summary['candidatePairs']
assert dict(counts)==summary['gaps']
assert len({r['reading'] for r in review})==len(review)
assert not any(r['existingIds'] for r in review+aliases)

def export(name,items):
    with (out/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['読み','表記','差分区分','関係の確認状況','一般的な読みの出典印','系列候補',
                                   '出典位置','語義の手がかり（原文・未校閲）','審査状態'])
        for r in items:
            hints=[];locations=[]
            for ref in r['evidenceLocations']:
                locations.append(ref['source']+':'+str(ref['location']))
                if ref['source']=='jmdict':
                    value=db.execute('SELECT details FROM evidence WHERE reading=? AND word=? AND source=? AND location=?',
                        (r['reading'],r['word'],ref['source'],str(ref['location']))).fetchone()
                    detail=json.loads(value[0]);hints.extend('/'.join(s['gloss']) for s in detail['senses'])
            w.writerow([r['reading'],r['word'],r['gap'],r['relation'],r['commonReading'],
                        '|'.join(r['families']),'|'.join(locations),' ; '.join(hints),'未審査'])

export('new-readings-first-2000.csv',review)
export('existing-readings-new-surfaces-1000.csv',aliases)
export('existing-pairs-sense-audit-500.csv',existing)
stats=dict(newReadingReviewPairs=len(review),sameReadingSurfaceReviewPairs=len(aliases),
           existingSenseAuditPairs=len(existing),newReadingsNotEndingN=len(new_usable),
           commonMarkedNewReadings=len(new_common))
(out/'review-summary.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
samples=['横断幕','一生懸命','売れ筋','栄養学','右往左往','当たり役','預かり証','あり合わせ','英訳','王宮']
examples=[]
for word in samples:
    r=db.execute("SELECT reading,word FROM candidates WHERE word=? AND gap='new-reading' AND jmdict=1 AND sudachi=1",(word,)).fetchone()
    if r:examples.append('・'+r[1]+'（'+r[0]+'）')
g=summary['gaps']
text=f'''# しりとり語彙の未収録候補調査（2026-11-16）

基準は最新参照 `origin/main` と一致する `{summary['baselineCommit'][:8]}`。
通常辞書 **{summary['baselineRows']:,}項目・{summary['baselineReadings']:,}種類の読み**から差分を取った。
辞書・配信・CPUの内容は変更していない。以下は出典に見つかった未審査候補で、採用数ではない。

| 区分 | 読み＋表記の組数 | 意味 |
| --- | ---: | --- |
| 新しい読みの候補 | {g['new-reading']:,} | 基準辞書に読みがない。同じ読みの複数表記を含む |
| 既存読みの新しい表記 | {g['same-reading-new-surface']:,} | 別表記・別語・別語義のどれかは要確認 |
| 既存の読み＋表記 | {g['existing-pair-sense-audit']:,} | 語義を網羅しているか確認するための監査対象 |

未収録候補は計 **{summary['missingPairs']:,}組**。
新しい読みだけで数えると **{summary['uniqueNewReadings']:,}種類**、
うち「ん」で終わらない読みは **{len(new_usable):,}種類**。
JMdictで一般的な読みの印がある新規読みは **{len(new_common):,}種類**。
一般的という印は、児童向け・高頻度・しりとりでの採用を保証しない。

| 未収録候補の出典 | 組数 |
| --- | ---: |
| JMdictとSudachiの両方 | {summary['missingBySource'].get('both',0):,} |
| JMdictのみ | {summary['missingBySource'].get('jmdict-only',0):,} |
| Sudachiのみ | {summary['missingBySource'].get('sudachi-only',0):,} |

## 確認を始めるファイル

- [新しい読み・先頭2,000種類](new-readings-first-2000.csv)：読みごとに1表記。一般的な読みの印、複数資料、生活系列の順で確認を進められる。
- [既存読みの新しい表記・先頭1,000組](existing-readings-new-surfaces-1000.csv)：別表記と別語義を確認する。
- [既存の読み＋表記・先頭500組](existing-pairs-sense-audit-500.csv)：説明の不足や一般語義の抜けを確認する。
- [数値・出典ハッシュ](summary.json)、[再開地点](checkpoint.json)。

CSVには語義の手がかりとなるJMdictの英語原文と、出典位置を添えた。
これは子ども向けの説明文ではなく、語義を照合するための管理資料。
複合語の系列は文字列一致による仮分類で、例えば「戸」が入るだけで家の設備と判定してはいけない。

## 今回見つかった例

以下は基準辞書に読みがなく、JMdictとSudachiの両方にある例。語義・用法の採用確認は次工程。

{chr(10).join(examples)}

## 次の収集方針

1. 新しい読みの一般語を先に確認する。難語・専門語・古語も対象に残し、難しさだけで却下しない。
2. 同じ出典項目の別表記候補は、語義と適用する読みを確認してから説明を共有する。単なる同音一致では結び付けない。
3. Sudachiだけにある語は、読み・表記の候補として扱い、独立した意味の根拠を補う。構成語の直訳で説明を量産しない。
4. 既存表記の語義監査を並行する。表記が収録済みでも、普通の意味が不足している場合がある。
5. 採否・理由・出典・説明・用法を `decisions.jsonl` に追記し、承認済みの項目だけを既存の取り込み手順に渡す。

「13万まであと何語」という上限は設けない。
追加成果は「項目数」「新しい読み」「別表記」「別語義」を分けて測る。

## 調査範囲と限界

JMdict 2026-10-05版の名詞語義、SudachiDict 20261015のsmall/coreの普通名詞を照合した。
Sudachi smallにはUniDic由来のデータが含まれる。独立した3辞書での照合ではない。
最新版UniDic単体、Sudachiの固有名詞全体、未登録入力ログは今回の集計に含めていない。
地名・駅名の任意パックも通常辞書とは別で、候補からの差し引きは行っていない。

不適切タグ・禁止語の一部は候補段階で除外するが、タグのない不適切語や文脈の確認が必要な語も残り得る。
古い読み・特殊な読み・数量表現・固有名詞の混入・名詞以外の用法も編集時に確認する。
「ん」で終わる語は候補に保持し、通常のしりとり回答とは区別する。
これらを未審査のままCPU・ヒント・子ども向け説明へ接続しない。

全件はローカルの `queue.jsonl` と `candidates.sqlite3` に保存。
SQLiteの `evidence` 表から、JMdictの項目ID・対象語義、Sudachiのファイル内行番号・元の表記・読みを確認できる。
これらと原本ZIPは再生成できる大きなキャッシュとしてGit対象外にし、要約・小規模確認リスト・スクリプト・採否記録を保持する。

## 再実行

```powershell
python -B -X utf8 scripts/fetch-shiritori-gap-sources.py
python -B -X utf8 scripts/build-shiritori-vocabulary-gaps.py --jmdict <jmdict-eng-3.6.2.jsonのパス>
python -B -X utf8 scripts/report-shiritori-vocabulary-gaps.py
```

索引作成後に中断した場合はビルドに `--resume-index` を付ける。
基準CSV・原本のSHA-256が変わっていれば再開を拒否し、最初から差分を取り直す。
再生成は `decisions.jsonl` を上書きしない。

## 出典

- [JMdict / EDRDG](https://www.edrdg.org/jmdict/j_jmdict.html)、[利用条件](https://www.edrdg.org/edrdg/licence.html)（CC BY-SA 4.0）。原本取得記録は `../general10000/source-metadata.json`。
- [SudachiDict公式](https://github.com/WorksApplications/SudachiDict)、[公式配布一覧](http://sudachi.s3-website-ap-northeast-1.amazonaws.com/sudachidict-raw/v1/)。取得ファイル・ハッシュは `source-downloads.json`。
- Sudachi由来の表記・読みはApache-2.0および付属の告知に従う。[LEGAL](SudachiDict-LEGAL) と [LICENSE](SudachiDict-LICENSE-2.0.txt) を保存。UniDic・NEologd等の由来と告知を保持する。
- 混合した管理台帳の各項目は `evidenceLocations.source` で出典を区別する。JMdict由来部分にはその利用条件が継続する。
'''
(out/'README.md').write_text(text,encoding='utf-8')
print(json.dumps(stats,ensure_ascii=False))
