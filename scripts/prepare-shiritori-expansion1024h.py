"""Freeze a daily-vocabulary batch before generating any pictures."""
import collections,csv,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/image-coverage/2026-10-18-expansion1024h'; NAME=OUT.name
save=lambda p,o:p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not (OUT/'plan.json').exists(),'Plan already frozen'
source=Path('C:/Users/user/.cache/shiritori-qa/dictionary/jmdict-eng-3.6.2.json');d=json.loads(source.read_text(encoding='utf-8'));byid={e['id']:e for e in d['words']}
a=json.loads((OUT/'editorial-candidates.json').read_text(encoding='utf-8'))
exclude=set(json.loads((OUT/'alternate-reading-exclusions.json').read_text()))|{1453,8896,0,2,19,60,105,124,136,143,147,154,160,166,177,184,194,196,199,220,221,236,242,249,260,266,277,285,289,291,292,295,303,311,331,336,341,346,356,378,387,394,412,439,443,450,459,466,470,479,489,499,504,507,576,591,598,603,609,621,637,645,652,659,674,681,684,685,692,693,698,700,707,708,711,716,719,725,730,739,741,777,783,784,791,800,813,818,821,822,832,833,842,845,854,860,874,875,882,884,889,892,896,899,905,906,910,927,928,938,944,966,971,976,1002,1010,1018,1021,1059,1079,1081,1117,1118,1122,1134,1158,1160,1175,1183,1184,1197,1232,1262,1269,1271,1283,1286,1287,1297,1308,1314,1334,1336,1347,1358,1361,1382,1387,1397,1398,1402,1423,1424,1437,1445,1454,1458,1465,1488,1494,1503,1506,1514,1515,1516,1519,1520,1549,1558,1562,1563,1564,1565,1571,1594,1601,1622,1626,1629,1637,1638,1642,1646,1651,1654,1670,1676,1683,1694,1705,1707,1725,1733,1744,1748,1763,1769,1772,1774,1775,1776,1780,1782,1783,1785,1790,1805,1806,1809,1819,1821,1823,1838,1851,1861,1862,1863,1870,1878,1879,1880,1882,1892,1912,1915,1916,1918,1919,1923,1930,1931,1940,1944,1958,1967,1975,1980,1988,1995,2002,2008,2009,2012,2013,2015,2019,2025,2027,2031,2036,2038,2039,2051,2057,2059,2062,2071,2091,2097,2098,2100,2104,2111,2113,2114,2117,2124,2125,2127,2128,2184,2198,2202,2203,2208,2219,2223,2235,2236,2238,2242,2244,2250,2253,2258,2263,2264,2270,2283,2287,2288,2295,2304,2317,2321,2322,2332,2339,2340,2357,2360,2361,2370,2402,2432,2443,2444,2449,2451,2454,2456,2466,2468,2486,2506,2524,2525,2528,2540,2545,2552,2561,2565,2584,2599,2629,2630,2641,2655,2657,2659,2663,2665,2679,2689,2694,2700,2704,2712,2714,2738,2755,2758,2766,2768,2774,2775,2780,2799,2810,2811,2818,2822,2827,2846,2850,2870,2874,2881,2884,2889,2899,2902,2904,2907,2962,2974,2983,2996,2999,3015,3016,3021,3028,3032,3051,3064,3071,3075,3087,3095,3114,3129,3138,3145,3162,3163,3164,3173,3181,3185,3188,3191,3195,3200,3201,3202,3205,3206,3213,3215,3232,3234,3237,3257,3262,3266,3267,3277,3287,3290,3294,3297,3308,3314,3324,3340,3346,3353,3378,3389,3391,3425,3426,3427,3428,3430,3433,3436,3444,3450,3455,3456,3462,3471,3481,3483,3484,3496,3506,3510,3514,3519,3522,3524,3525,3542,3547,3554,3556,3560,3567,3569,3571,3578,3586,3588,3589,3594}
# The large set above is the conservative middle-grade pool, not exclusions.
mid=exclude-set(json.loads((OUT/'alternate-reading-exclusions.json').read_text()))-{1453,8896}
exclude=set(json.loads((OUT/'alternate-reading-exclusions.json').read_text()))|{1453,8896,177,236,239,249,260,262,266,277,285,289,303,627,739,741,775,787,791,792,793,935,1819,1959,2372,2629,2630,2847,2996,2999,3075,3095,3276,3471,8356,8357,8365,8834,8856,5270,5272,5742,5908,5912,5914,6192}
# Avoid counting families of counters, alternate address forms and duplicate synonymous spellings as 1024 new concepts.
# Keep a few basic family words that already have a direct useful everyday sense.
rows=list(csv.DictReader((ROOT/'whitelist.csv').open(encoding='utf-8-sig')));existing={r['reading'] for r in rows}
blocked=[]
for line in (ROOT/'blacklist.txt').read_text(encoding='utf-8').splitlines():
 if line.strip() and not line.startswith('#'):blocked.append(line.strip())
reserved=set()
for p in (ROOT/'data/image-coverage').glob('*/reservation.json'):
 if p.parent==OUT:continue
 def readings(o):
  if isinstance(o,dict):
   for k,v in o.items():
    if k=='reading' and isinstance(v,str):yield v
    else:yield from readings(v)
  elif isinstance(o,list):
   for v in o:yield from readings(v)
 reserved.update(readings(json.loads(p.read_text(encoding='utf-8'))))
items=[];skipped=[]
for x in a:
 i=x['candidateIndex'];rd=x['reading']
 reason='alternate-or-editorial-exclusion' if i in exclude else 'existing-or-reserved' if rd in existing|reserved else 'blacklist' if any(b in rd for b in blocked if ':' not in b) else None
 if reason:skipped.append(dict(reading=rd,word=x['word'],reason=reason));continue
 x=dict(x,grade=2 if i in mid else 1);items.append(x)
# Retain household/school words before more specialized terms; never manufacture filler.
items.sort(key=lambda x:(x['grade'],len(x['reading']),x['reading']))
skipped.extend(dict(reading=x['reading'],word=x['word'],reason='reserve-for-next-batch') for x in items[1024:]);items=items[:1024]
assert len(items)==1024,len(items)
items.sort(key=lambda x:x['reading'])
base=(ROOT/'whitelist.csv').read_bytes();(OUT/'registration-baseline.csv').write_bytes(base)
for slot,x in enumerate(items,1):
 e=byid[x['entryId']];s=e['sense'][x['senseIndex']]
 x.update(slot=slot,id=len(rows)+slot,level=1 if x['grade']==1 else 2,sheet=(slot-1)//16+1,tileIndex=(slot-1)%16+1,filename=f"expansion1024h-word-{len(rows)+slot}.png",assignment='new',reviewStatus='editorially-reviewed',
 lexicalSource=f"JMdict {e['id']} / {d['dictDate']} / https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e={e['id']}",
 meaningReason='日常で使う対象語義を選び日本語の説明を独自に作成。'+x['meaning'],
 ageReason='家庭・学校・遊びなどで具体的に説明できる日常語義。' if x['grade']==1 else '一般語だが語の名前や内容に中学年程度の学習・経験も必要。低学年用CPUには混ぜない。',
 imageReason='選択した語義の具体物または生活場面を描いた専用イラスト。',gameEndingN=x['reading'].endswith('ん'),definitionAuthor='独自作成（2026-10-18）',sources=[f"https://www.edrdg.org/jmdictdb/cgi-bin/entr.py?svc=jmdict&e={e['id']}"])
plan=dict(batch=NAME,date='2026-10-18',baselineRows=len(rows),baselineSha256=hashlib.sha256(base).hexdigest(),sourceDate=d['dictDate'],sourceSha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),items=items)
save(OUT/'plan.json',plan);save(OUT/'selection-review.json',dict(considered=len(a),selected=1024,skipped=skipped));save(OUT/'reservation.json',dict(batch=NAME,status='planned',items=[dict(reading=x['reading'],word=x['word']) for x in items]))
header='''Use case: illustration-story. Edit the attached 2048x2048 equal 4 by 4 template. Paint EXACTLY sixteen independent vocabulary pictures, row-major left to right then top to bottom. Preserve all FIVE horizontal and FIVE vertical continuous straight pure MAGENTA #ff00ff grid lines INCLUDING OUTER FRAME, exact positions and thickness, equal cell sizes and canvas dimensions. Magenta ONLY in lines. Paint only white panel interiors. Warm clear children's picture-book style, recognizable accurate subjects and anatomy. Use each cell generously, no required large white margins. Keep every object and shadow wholly inside its cell. NO words, letters, numerals, logos, watermarks, labels or captions. Abstract words use a simple concrete daily scene that distinguishes the requested meaning. No imitation of famous characters. Do not depict unsafe behavior as something to copy. Each of the following SIXTEEN panels must match the exact meaning:\n'''
sheets=[]
for n in range(64):
 group=items[n*16:(n+1)*16];prompt=header+'\n'.join(f"{k+1}. {x['word']}: {x['meaning']}" for k,x in enumerate(group))
 sh=dict(sheet=n+1,sourceSheet=f'sheets/expansion1024h-sheet{n+1:02}.png',tiles=group,prompt=prompt);sheets.append(sh)
 (OUT/f'sheet{n+1:02}.prompt.txt').write_text(prompt,encoding='utf-8')
save(OUT/'sheets.json',sheets)
print(json.dumps(dict(selected=len(items),gradeCounts=dict(collections.Counter(x['grade'] for x in items)),endingN=sum(x['gameEndingN'] for x in items),sheets=len(sheets)),ensure_ascii=False))
