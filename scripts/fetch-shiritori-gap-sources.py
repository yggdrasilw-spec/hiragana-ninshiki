"""Fetch pinned official discovery sources; hashes recorded for repeatability."""
import datetime, hashlib, json, urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]
out=root/'data/vocabulary-gap';cache=out/'sources';cache.mkdir(parents=True,exist_ok=True)
records=[]
for name,url,target in [
    ('small_lex.zip','https://sudachi.s3.ap-northeast-1.amazonaws.com/sudachidict-raw/v1/20261015/small_lex.zip',cache/'small_lex.zip'),
    ('core_lex.zip','https://sudachi.s3.ap-northeast-1.amazonaws.com/sudachidict-raw/v1/20261015/core_lex.zip',cache/'core_lex.zip'),
    *[(n,'https://raw.githubusercontent.com/WorksApplications/SudachiDict/develop/'+n,out/('SudachiDict-'+n))
      for n in ['LEGAL','LICENSE-2.0.txt','README.md']]
]:
    if not target.exists():
        # Do not overwrite the original on a failed/partial download.
        temporary=target.with_suffix(target.suffix+'.download')
        with urllib.request.urlopen(url,timeout=60) as response, temporary.open('wb') as stream:
            while data:=response.read(1024*1024):stream.write(data)
        temporary.replace(target)
    records.append(dict(file=target.relative_to(root).as_posix(),url=url,
        bytes=target.stat().st_size,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
(out/'source-downloads.json').write_text(json.dumps(dict(
    checkedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    distributionPage='http://sudachi.s3-website-ap-northeast-1.amazonaws.com/sudachidict-raw/v1/',
    version='20261015',files=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Verified pinned source cache and recorded hashes.')
