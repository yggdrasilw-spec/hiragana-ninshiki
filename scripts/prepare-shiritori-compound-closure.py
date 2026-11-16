"""Generate source-grounded compound descriptions with explicit structural rules.

Every compound must already be an independent JMdict headword with its own
applicable noun sense. Both the stem's POS and the English sense must support
the rule. Results remain provisional level 4 until individually edited.
"""
import collections,csv,hashlib,json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'data/lexical-expansion';S=R/'data/general10000/sources'
norm=lambda t:unicodedata.normalize('NFKC',t)
hira=lambda t:''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in norm(t))
RULES=[
 ('訓練','vs',r'training|drill|exercise','{stem}の仕方を身に付けるための練習。'),
 ('練習','vs',r'practice|training|exercise','{stem}がうまくできるように、繰り返し行うこと。'),
 ('用紙','vs',r'paper|form|sheet','{stem}に使う紙。'),
 ('用品','vs',r'goods|supplies|equipment|article|item','{stem}に使う品物。'),
 ('道具','vs',r'tool|instrument|equipment|utensil','{stem}に使う道具。'),
 ('装置','vs',r'device|apparatus|equipment|system|plant|unit','{stem}を行うための装置。'),
 ('機械','vs',r'machine|machinery|apparatus|device','{stem}を行うための機械。'),
 ('施設','vs',r'facilit|centre|center|institution|plant','{stem}を行うための建物や設備。'),
 ('時間','vs',r'time|hour|duration','{stem}を行う時間。'),
 ('期間','vs',r'period|term|duration','{stem}を行う期間。'),
 ('計画','vs',r'plan|project|scheme|program','{stem}を行うための計画。'),
 ('準備','vs',r'prepar','{stem}を行う前に、必要なことを整えること。'),
 ('制度','vs',r'system|scheme','{stem}を行うための決まりや仕組み。'),
 ('事業','vs',r'business|enterprise|project|service|industr','{stem}を行う事業。'),
 ('作業','vs',r'work|operation|task','{stem}を行う作業。'),
 ('工場','vs',r'factory|plant|mill|works','{stem}を行う工場。'),
 ('工事','vs',r'construction|work|engineering','{stem}を行う工事。'),
 ('辞典','n',r'dictionary|lexicon','{stem}について調べるための辞典。'),
 ('図鑑','n',r'book|dictionary|encyclop|guide','{stem}の種類などを、図や説明で調べる本。'),
 ('研究','n',r'research|study|studies','{stem}について詳しく調べ、考えること。'),
 ('機','vs',r'machine|apparatus|device|instrument|equipment|printer|generator','{stem}に使う機械。'),
 ('器','vs',r'apparatus|device|instrument|equipment|meter|detector|utensil|tool','{stem}に使う器具や装置。'),
 ('室','vs',r'room|chamber|office|lab|studio','{stem}を行うための部屋。'),
 ('所','vs',r'place|office|station|centre|center|facility|plant|room|shop|house','{stem}を行う場所や施設。'),
 ('場','vs',r'place|ground|site|area|field|plant|station|hall|room','{stem}を行う場所。'),
 ('料','vs',r'fee|charge|fare|dues|payment','{stem}のために支払うお金。'),
 ('代','vs',r'fee|charge|fare|cost|expense|payment','{stem}のために支払うお金。'),
 ('費','vs',r'fee|charge|cost|expense|expenditure','{stem}のために必要になるお金。'),
 ('員','vs',r'person|worker|officer|member|employee|clerk|staff|inspector|assistant|attendant|operator','{stem}の仕事や役割を受け持つ人。'),
 ('者','vs',r'person|worker|officer|member|employee|clerk|staff|inspector|assistant|attendant|operator|\b[a-z]+(?:er|or|ist)\b','{stem}をする人や、{stem}をした人。'),
 ('法','vs',r'method|technique|procedure|way of|process','{stem}を行う方法。'),
 ('術','vs',r'technique|art|skill|method','{stem}を行う技術。'),
 ('業','vs',r'business|trade|industr|service|profession','{stem}を行う仕事や産業。'),
 ('会','vs',r'meeting|session|conference|gathering|convention','{stem}のために開く集まり。'),
 ('権','vs',r'right|authority','{stem}をすることが認められる権利。'),
 ('店','n',r'\b(?:shop|store|dealer)\b','{stem}などを扱う店。'),
 ('屋','n',r'\b(?:shop|store|seller|dealer|vendor)\b','{stem}を扱う店や、その店の人。')
]
def main():
 raw=(R/'whitelist.csv').read_bytes();old=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()));pairs={(x['reading'],norm(x['word'])) for x in old};readings={x['reading'] for x in old}
 jm=json.loads((S/'jmdict-eng-3.6.2.json').read_text(encoding='utf-8'));forms=collections.defaultdict(list)
 forbidden={'arch','obs','rare','vulg','derog','sl','dated','sens','X'}
 unsafe=re.compile(r'性交|性行為|性的|性器|陰茎|膣|睾丸|精液|射精|自慰|売春|娼婦|ポルノ|猥褻|わいせつ|強姦|レイプ|自殺|自傷|麻薬|コカイン|ヘロイン|覚醒剤|差別語|蔑称|侮蔑|卑語|卑俗|黒ん坊|土人|きちがい|処刑|殺人|拷問|屠殺|暗殺|大人のおもちゃ|大人の玩具|\b(?:sex|sexual|erotic|pornography|vagina|penis|scrotum|masturbation|prostitution|suicide|execution|torture)\b',re.I)
 def allowed(s):return not s['dialect'] and not set(s['misc']) & forbidden and not unsafe.search(' '.join(g['text'] for g in s['gloss']))
 for e in jm['words']:
  for number,s in enumerate(e['sense'],1):
   if not allowed(s):continue
   pos=set(s['partOfSpeech']);noun=bool(pos & {'n','n-vs','n-t','n-adv'});vs=bool(pos & {'vs','vs-i','vs-s','n-vs'})
   if not noun:continue
   for w in e['kanji']+e['kana']:
    if '*' not in s['appliesToKanji'] and w['text'] not in s['appliesToKanji']:continue
    forms[w['text']].append(dict(entryId=e['id'],senseNumber=number,vs=vs,n=not bool(pos & {'adj-no','adj-na','adj-f','adj-t','adv'}),glosses=[g['text'] for g in s['gloss'] if g['lang']=='eng']))
 blocked=[]
 for line in (R/'blacklist.txt').read_text(encoding='utf-8').splitlines():
  line=line.strip()
  if not line or line.startswith('#'):continue
  m=re.match(r'(exact|contains)\s*[:=]\s*(.*)',line,re.I);blocked.append((m[1].lower(),hira(m[2])) if m else ('contains',hira(line)))
 result={};counts=collections.Counter()
 for e in jm['words']:
  for k in e['kana']:
   reading=hira(k['text'])
   if not re.fullmatch('[ぁ-ゖー]{1,30}',reading) or reading.startswith('ん') or set(k['tags']) & {'ik','ok','rk','gikun'}:continue
   if any(reading==p if mode=='exact' else p in reading for mode,p in blocked):continue
   for w in e['kanji'] or [dict(text=k['text'],tags=[])]:
    word=w['text'];key=(reading,norm(word))
    if key in pairs or key in result or unsafe.search(word) or re.search(r'[\s,\r\n\t()（）/／0-9A-Za-z−-]',word):continue
    if set(w['tags']) & {'iK','ik','oK','rk'}:continue
    if '*' not in k['appliesToKanji'] and word not in k['appliesToKanji']:continue
    senses=[(i,s) for i,s in enumerate(e['sense'],1) if allowed(s) and set(s['partOfSpeech']) & {'n','n-vs','n-t','n-adv'} and ('*' in s['appliesToKana'] or k['text'] in s['appliesToKana']) and ('*' in s['appliesToKanji'] or word in s['appliesToKanji'])]
    for suffix,stempos,english,template in RULES:
     if not word.endswith(suffix):continue
     stem=word[:-len(suffix)]
     if len(stem)<2 or stem not in forms or unsafe.search(stem):continue
     stems=[x for x in forms[stem] if x[stempos]]
     if not stems:continue
     evidence=[dict(entryId=e['id'],senseNumber=i,matchedGlosses=[g['text'] for g in s['gloss'] if g['lang']=='eng' and re.search(english,g['text'],re.I)]) for i,s in senses]
     evidence=[x for x in evidence if x['matchedGlosses']]
     if not evidence:continue
     normalized=lambda t:re.sub(r'[^a-z0-9 ]',' ',t.lower().replace('-',' '))
     # A suffix and a noun tag alone do not establish a compound's meaning:
     # storey != store, and latest research is not research about "latest".
     aligned=[]
     for se in stems:
      matched=[]
      for sg in se['glosses']:
       sg=re.sub(r'\([^)]*\)','',sg).strip()
       sg=re.sub(r'^(?:to |the |a |an )','',sg)
       text=' '.join(normalized(sg).split())
       if len(text)<3:continue
       for ev in evidence:
        for full in ev['matchedGlosses']:
         if re.search(r'\b'+re.escape(text)+r'\b',normalized(full)):matched.append(dict(stemGloss=sg,compoundGloss=full))
      if matched:aligned.append(dict(**se,semanticAlignment=matched))
     if not aligned:continue
     meaning=template.format(stem=stem)
     result[key]=dict(reading=reading,word=word,meaning=meaning,entryId=e['id'],evidence=evidence,stem=stem,stemEvidence=aligned,
       rule=suffix+'-'+stempos,englishPattern=english,template=template,grade=4,gap='new-reading' if reading not in readings else 'new-spelling',
       reviewStatus='source-and-structure-checked-provisional',definitionAuthor='複合語の構造に基づく独自説明',common=k['common'] or w.get('common',False))
     counts[suffix]+=1;break
 rows=sorted(result.values(),key=lambda x:(x['gap']!='new-reading',not x['common'],len(x['reading']),x['reading'],x['word']))
 (D/'compound-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows),encoding='utf-8')
 print(json.dumps(dict(candidates=len(rows),newReadings=len({x['reading'] for x in rows}-readings),rules=counts,baselineSha256=hashlib.sha256(raw).hexdigest()),ensure_ascii=False))
 for x in rows[:120]:print(x['word'],x['reading'],x['meaning'])
if __name__=='__main__':main()
