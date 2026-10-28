const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const normal=require('../scripts/build-shiritori-delivery.cjs').build(root);
const pack=require('../scripts/build-shiritori-geography.cjs').build(root,normal);
const Catalog=require('../shiritori-dictionary.js'),vocabulary=require('../shiritori-vocabulary.js');
(async()=>{
  const requests=[],files=new Map(normal.files);for(const [name,text] of pack.files)files.set('japan-places/'+name,text);
  let failPack=false;
  const dictionary=new Catalog({base:'',fetcher:async url=>{
    requests.push(url);if(failPack&&url==='japan-places/index.json')throw Error('offline');
    assert.ok(files.has(url),url);return {ok:true,json:async()=>JSON.parse(files.get(url))};
  }});
  const initial=await dictionary.init();assert.equal(initial.length,normal.rows.length);assert.deepEqual(requests,['index.json']);
  const index=await dictionary.setJapanPlaces(true);
  const total=new Set([...normal.rows,...pack.rows].map(r=>r.reading));assert.equal(index.length,total.size);
  assert.equal(requests.length,2,'Enabling downloads only the pack index');
  assert.equal(pack.manifest.meanings,95520);assert.equal(pack.rows.length,85326);
  const all=vocabulary.categories,genres=Object.keys(all);
  for(let level=1;level<=5;level++)for(const chosen of [genres,...genres.map(g=>[g]),['place','japanPlace'],['animal','japanPlace'],[]]){
    const expected=new Set();
    for(const r of [...normal.rows,...pack.rows])if(r.genres.some((g,i)=>r.meaningLevels[i]<=level&&chosen.includes(g)))expected.add(r.reading);
    assert.equal(dictionary.count(level,chosen),expected.size,`${level} ${chosen}`);
  }
  const first=await dictionary.reading('しんしらおか');assert.ok(first.words.includes('新白岡'));assert.ok(first.imagequeries.some(q=>q.source?.license==='CC BY 4.0'));
  const duplicate=normal.rows.find(r=>pack.rows.some(g=>g.reading===r.reading)&&r.words.length>1);
  const merged=await dictionary.reading(duplicate.reading),geo=pack.rows.find(r=>r.reading===duplicate.reading);
  assert.equal(merged.words.length,duplicate.words.length+geo.words.length,'Normal and geography homophones retain separate senses');
  assert.equal(new Set(merged.words.map((w,i)=>w+'\t'+merged.meanings[i])).size,merged.words.length);
  const suggestions=vocabulary.suggestions('しんしらおが',index,{level:5});assert.ok(suggestions.some(r=>r.reading==='しんしらおか'));
  const rows=await dictionary.prepare('ぬ',5,['japanPlace']);assert.ok(rows.length);assert.ok(rows.every(r=>r.reading[0]==='ぬ'&&r.genres.every(g=>g==='japanPlace')));
  assert.equal((await dictionary.prepare('ぬ',1,['japanPlace'])).length,0);
  const unknown=pack.rows.find(r=>!normal.rows.some(n=>n.reading===r.reading)).reading;
  await dictionary.setJapanPlaces(false);assert.equal(dictionary.lookup(unknown),null);assert.ok(dictionary.lookup('りんご'));assert.equal(dictionary.index.size,normal.rows.length);
  failPack=true;await assert.rejects(dictionary.setJapanPlaces(true),/offline/);assert.equal(dictionary.extra,null);assert.equal(dictionary.index.size,normal.rows.length);
  failPack=false;await dictionary.setJapanPlaces(true);assert.ok(dictionary.lookup(unknown));
  for(const [name,body] of pack.files)assert.equal(fs.readFileSync(path.join(root,'data/shiritori-delivery/japan-places',name),'utf8'),body);
  const snapshot=JSON.parse(fs.readFileSync(path.join(root,'data/japan-places/metadata.json'),'utf8'));
  assert.equal(snapshot.categories.station,8499);assert.equal(snapshot.categories.town,83452);
  console.log(JSON.stringify({passed:true,normalReadings:normal.rows.length,geographyMeanings:95520,geographyReadings:85326,totalUniqueReadings:total.size,packChunks:pack.manifest.chunks.length,packIndexBytes:Buffer.byteLength(pack.files.get('index.json')),checks:['optional-load','source-attribution','homophones','95k-genre-counts','fuzzy-search','disable','retry']}));
})().catch(e=>{console.error(e);process.exitCode=1;});
