"""Cache public name references, without importing third-party artwork."""
import concurrent.futures,hashlib,json,urllib.request
from pathlib import Path
CACHE=Path('C:/Users/user/.cache/shiritori-qa/expansion512e-sources')
CACHE.mkdir(parents=True,exist_ok=True)
URLS={
 'sanrio-names.json':'https://www.sanrio.co.jp/system/json/characters_yomi.json',
 'hokuto-characters.html':'https://hokuto-no-ken.jp/hokuto_archives',
 'hunter.html':'https://www.ntv.co.jp/hunterhunter/character/index.html',
 'hunter-ant.html':'https://www.ntv.co.jp/hunterhunter/character/kimera.html',
 'hunter-spider.html':'https://www.ntv.co.jp/hunterhunter/character/genei.html',
 'dragon.html':'https://www.toei-anim.co.jp/tv/dragon/character/',
 'dragon-super.html':'https://www.toei-anim.co.jp/tv/dragon_s/chara/',
 'dragon-z.html':'https://www.toei-anim.co.jp/tv/dragonz/character/',
 'seed.html':'https://gundam-official.com/seed/seed/mecha/',
 'seed-destiny.html':'https://gundam-official.com/seed/destiny/mecha/',
 'gwitch.html':'https://g-witch.net/mobile-suit/',
 'gqux.html':'https://gundam-official.com/gquuuuuux/mecha/',
 'jump.html':'https://www.shonenjump.com/j/sp_jumpbookstore/ichiran.html',
}
URLS.update({f'hunter-other{n}.html':f'https://www.ntv.co.jp/hunterhunter/character/other_0{n}.html' for n in range(1,7)})
def fetch(kv):
 name,url=kv;target=CACHE/name
 if not target.exists():target.write_bytes(urllib.request.urlopen(url,timeout=30).read())
 return dict(file=name,url=url,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=target.stat().st_size)
records=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(fetch,URLS.items()))
root=Path(__file__).resolve().parents[1]
out=root/'data/image-coverage/2026-10-15-expansion512e/source-fetch.json'
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(files=len(records),artworkDownloaded=0)))
