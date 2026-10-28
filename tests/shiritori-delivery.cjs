const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const {build}=require('../scripts/build-shiritori-delivery.cjs');
const Dictionary=require('../shiritori-dictionary.js');
const small={'ぁ':'あ','ぃ':'い','ぅ':'う','ぇ':'え','ぉ':'お','ゃ':'や','ゅ':'ゆ','ょ':'よ','っ':'つ','ゎ':'わ','ゕ':'か','ゖ':'け'};
const head=s=>small[s[0]]||s[0]||'';
(async()=>{
  const {rows,files,manifest}=build(root),calls=[];let fail='';
  const dictionary=new Dictionary({head,base:'',fetcher:async url=>{
    calls.push(url);if(fail===url)throw Error('offline');
    return {ok:true,json:async()=>JSON.parse(files.get(url))};
  }});
  const index=await dictionary.init();
  assert.equal(index.length,rows.length);assert.equal(calls.length,1);
  assert.ok(index.every(r=>r._indexOnly&&!r.meanings[0]),'Startup has no definitions/images');
  // Every reading retains every homophone, editorial level and image pairing.
  const delivered=manifest.chunks.flatMap(c=>JSON.parse(files.get(c.file)));
  assert.deepEqual(new Map(delivered.map(r=>[r.reading,r])),new Map(JSON.parse(JSON.stringify(rows)).map(r=>[r.reading,r])));
  const categories=Object.keys(require('../shiritori-vocabulary.js').categories);
  for(let level=1;level<=5;level++)for(const genres of [categories,...categories.map(g=>[g]),['animal','plant'],[]]){
    const expected=rows.filter(r=>r.genres.some((g,i)=>genres.includes(g)&&r.meaningLevels[i]<=level)).length;
    assert.equal(dictionary.count(level,genres),expected,`${level} ${genres}`);
  }
  const entry=index.find(r=>head(r.reading)==='り'),file=manifest.chunks[entry.chunk].file;
  const before=calls.length;
  const [a,b]=await Promise.all([dictionary.reading(entry.reading),dictionary.reading(entry.reading)]);
  assert.equal(a,b);assert.equal(calls.length,before+1,'Concurrent requests share one download');
  assert.deepEqual(a,delivered.find(r=>r.reading===entry.reading));
  assert.ok(!a._indexOnly);
  const target=index.find(r=>!dictionary.loaded.has(r.chunk));
  fail=manifest.chunks[target.chunk].file;
  await assert.rejects(dictionary.reading(target.reading),/offline/);
  assert.ok(dictionary.lookup(target.reading),'Failure never removes membership');
  fail='';assert.ok(await dictionary.reading(target.reading),'Failed requests are retryable');
  for(let id=0;id<30;id++)await dictionary.chunk(id);
  assert.ok(dictionary.loaded.size<=12,'Bounded payload memory');
  assert.ok(await dictionary.reading(entry.reading),'Evicted definitions can be loaded again');
  assert.equal(await dictionary.reading('みとうろくのことばです'),null);
  const learned={reading:'みとうろくのことばです',words:['新語'],meanings:['説明'],imagequeries:[{}],level:4,meaningLevels:[4]};
  dictionary.add(learned);assert.equal(await dictionary.reading(learned.reading),learned);
  for(const [name,body] of files)assert.equal(fs.readFileSync(path.join(root,'data/shiritori-delivery',name),'utf8'),body);
  console.log(JSON.stringify({passed:true,readings:rows.length,meanings:rows.reduce((n,r)=>n+r.words.length,0),countChecks:5*(categories.length+3),chunks:manifest.chunks.length,maxChunkReadings:Math.max(...manifest.chunks.map(c=>c.count))}));
})().catch(e=>{console.error(e);process.exitCode=1;});
