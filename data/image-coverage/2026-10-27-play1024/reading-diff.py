import json,re
from pathlib import Path
H=Path(__file__).resolve().parent
a=json.loads((H/'2026-10-27-play1024.review.json').read_text(encoding='utf-8'))
def hira(s):return ''.join(chr(ord(c)-96) if 'ァ'<=c<='ヶ' else c for c in s)
for x in json.loads((H/'dm-readings.json').read_text(encoding='utf-8')):
 if not x.get('heading') or not x['heading'].startswith('《'):continue
 r=re.sub(r'[^()《》]+\(([^)]+)\)',lambda m:m[1],x['heading'].split('》')[0])
 # Apply ruby substitution in word fragments, retaining preceding non-ruby text.
 r=x['heading'].split('》')[0].lstrip('《')
 for ruby in x.get('ruby',[]):
  base,reading=ruby.rsplit('(',1);r=r.replace(ruby,reading.rstrip(')'))
 r=hira(re.sub('[ ・「」『』～〜―－\-“”]','',r))
 if not re.fullmatch('[ぁ-ゖー]+',r):continue
 row=next((y for y in a if y['word']==x['word']),None)
 if row and row['reading']!=r:print(json.dumps(dict(word=x['word'],before=row['reading'],after=r),ensure_ascii=False))
