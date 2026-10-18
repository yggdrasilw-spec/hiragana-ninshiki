"""Fetch public Japanese naming evidence; keep source text out of the dictionary.

The API cache is research evidence, not an automatic approval or translation.
Run once before editorial review; requests are read-only and resumable.
"""
import json,time,urllib.request,urllib.parse,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/dictionary-imports/2026-10-19-mythology512'
OUT=ROOT/'qa-output/mythology512-research'
OUT.mkdir(parents=True,exist_ok=True)

def candidates():
 group=''
 for line in BASE.with_suffix('.candidates.txt').read_text(encoding='utf-8').splitlines():
  if not line or line.startswith('#'):continue
  if line.startswith('['):group=line[1:-1];continue
  fields=line.split('|');word,kind,detail=fields[:3]
  reading=fields[3] if len(fields)>3 else ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in word).replace('・','')
  yield dict(group=group,word=word,kind=kind,detail=detail,reading=reading)

TITLES={
 'ヘラ':'ヘーラー','パン':'パーン','レア':'レアー','アトラス':'アトラース',
 'エリス':'エリス (神話)','テティス':'テティス (ギリシア神話)',
 'カロン':'カローン','トリトン':'トリートーン','プロテウス':'プローテウス',
 'イリス':'イーリス','ヘベ':'ヘーベー','テュケ':'テュケー',
 'クロト':'クロートー','ラケシス':'ラケシス','クレイオ':'クレイオー',
 'タレイア':'タレイア (ムーサ)','エラト':'エラトー',
 'メルポメネ':'メルポメネー','テルプシコレ':'テルプシコレー',
 'ウラニア':'ウーラニアー','プシュケ':'プシューケー',
 'トール':'トール','ウル':'ウル (北欧神話)','ヘル':'ヘル (北欧神話)',
 'ノート':'ノート (北欧神話)','ソール':'ソール (北欧神話)','マーニ':'マーニ',
 'グラム':'グラム (北欧神話)','フレイ':'フレイ','ウルズ':'ウルズ',
 'ヤマ':'ヤマ (インド神話)','ソーマ':'ソーマ','アグニ':'アグニ',
 'ラー':'ラー','アメン':'アメン','ホルス':'ホルス','セト':'セト',
 'シュー':'シュー (エジプト神話)','ヌト':'ヌト','ヌン':'ヌン',
 'ハピ':'ハピ','コンス':'コンス','グラ':'グラ (メソポタミア神話)',
 'ウツ':'ウトゥ','ナンナ':'ナンナ (メソポタミア神話)',
 'ルー':'ルー (神)','リル':'リール (ケルト神話)','ブラン':'ブラン (ケルト神話)',
 'リュー':'スェウ・スァウ・ゲフェス','メイヴ':'メイヴ','ナイシ':'ノイシュ',
 'カネ':'カーネ','クー':'クー (ハワイ神話)','ロノ':'ロノ','サンポ':'サンポ',
 'ペレ':'ペレ (ハワイ神話)','ヒイアカ':'ヒイアカ','マウイ':'マウイ (ポリネシア神話)',
 'ミスラ':'ミスラ','ロスタム':'ロスタム','ザール':'ザール (イラン神話)',
 'サテト':'サテト','オヤ':'オヤ (ヨルバ神話)',
 'ミネルウァ':'ミネルウァ','ウェヌス':'ウェヌス','ケレス':'ケレース',
 'ディアナ':'ディアーナ','ヤヌス':'ヤーヌス','アイネアス':'アイネイアース',
 'レムス':'レムス','ロムルス':'ロームルス',
}

def fetch(index,items,language='ja'):
 target=OUT/(f'part-{index:02}.json' if language=='ja' else f'en-part-{index:02}.json')
 if target.exists():return json.loads(target.read_text(encoding='utf-8'))
 english=json.loads(BASE.with_suffix('.english-titles.json').read_text(encoding='utf-8'))
 titles=[(TITLES if language=='ja' else english).get(x['word'],x['word']) for x in items]
 params=dict(action='query',format='json',redirects='1',prop='extracts|pageprops',
             exintro='1',explaintext='1',exchars='1100',exlimit='20',titles='|'.join(titles))
 url='https://'+language+'.wikipedia.org/w/api.php?'+urllib.parse.urlencode(params)
 req=urllib.request.Request(url,headers={'User-Agent':'ShiritoriVocabularyResearch/1.0'})
 for attempt in range(4):
  try:
   with urllib.request.urlopen(req,timeout=45) as response:data=json.load(response)
   break
  except urllib.error.HTTPError as error:
   if error.code not in (429,502,503) or attempt==3:raise
   time.sleep(max(int(error.headers.get('Retry-After','10')),10)*(attempt+1))
  except (urllib.error.URLError,TimeoutError):
   if attempt==3:raise
   time.sleep(5*(attempt+1))
 if 'error' in data:raise ValueError(data['error'])
 target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return data

def main():
 items=list(candidates());parts=[items[i:i+20] for i in range(0,len(items),20)]
 results=[]
 for index,part in enumerate(parts,1):
  cached=(OUT/f'part-{index:02}.json').exists()
  results.append(fetch(index,part))
  if not cached:time.sleep(2)
 evidence=[]
 for part,data in zip(parts,results):
  query=data['query'];redirects={r['from']:r['to'] for r in query.get('redirects',[])}
  pages={p['title']:p for p in query['pages'].values()}
  for item in part:
   title=TITLES.get(item['word'],item['word']);seen=set()
   while title in redirects and title not in seen:seen.add(title);title=redirects[title]
   page=pages.get(title,{})
   evidence.append(dict(**item,title=title,url='https://ja.wikipedia.org/wiki/'+urllib.parse.quote(title),
                        missing='missing' in page or not page,disambiguation='disambiguation' in page.get('pageprops',{}),
                        extract=page.get('extract',''),revisionDate='2026-10-19'))
 english=json.loads(BASE.with_suffix('.english-titles.json').read_text(encoding='utf-8'))
 fallback=[x for x in evidence if x['word'] in english]
 for offset in range(0,len(fallback),20):
  part=fallback[offset:offset+20];data=fetch(offset//20+1,part,'en')['query']
  redirects={r['from']:r['to'] for r in data.get('redirects',[])}
  pages={p['title']:p for p in data['pages'].values()}
  for item in part:
   title=english[item['word']];seen=set()
   while title in redirects and title not in seen:seen.add(title);title=redirects[title]
   page=pages.get(title,{})
   item['englishEvidence']=dict(title=title,url='https://en.wikipedia.org/wiki/'+urllib.parse.quote(title),
      missing='missing' in page or not page,disambiguation='disambiguation' in page.get('pageprops',{}),extract=page.get('extract',''))
  time.sleep(2)
 (OUT/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(candidates=len(items),needsTitleReview=[dict(word=x['word'],title=x['title'],missing=x['missing'],disambiguation=x['disambiguation']) for x in evidence if x['missing'] or x['disambiguation'] or not x['extract']]),ensure_ascii=False))
if __name__=='__main__':main()
