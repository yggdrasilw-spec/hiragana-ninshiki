const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),details=require('../shiritori-mrs-details.js');
const {rows,files,manifest}=require('../scripts/build-shiritori-delivery.cjs').build(root);
assert.equal(details.entries.length,207);
const byReading=new Map(rows.map(r=>[r.reading,r]));
for(const e of details.entries){
 const r=byReading.get(e.reading),i=r.words.findIndex((w,i)=>w===e.word&&r.meanings[i]===e.meaning);
 assert(i>=0,e.word);assert.equal(r.imagequeries[i].source.details,e.details);
 assert.equal(r.imagequeries[i].source.url,e.source.url);assert.match(e.source.url,/^https:\/\//);
 assert(e.details.length>=30);assert.equal(r.imagequeries[i].mode,'none');assert(!r.imagequeries[i].asset);
 assert.equal(r.meaningLevels[i],5);assert.equal(r.genres[i],'entertainment');
 const delivered=JSON.parse(files.get(manifest.chunks[manifest.readings.find(x=>x[0]===e.reading)[2]].file)).find(r=>r.reading===e.reading);
 assert.equal(delivered.imagequeries[i].source.details,e.details);
}
for(const word of ['French','Midnight','Mrs. GREEN APPLE','Variety','The White Lounge']){
 const entries=details.entries.filter(e=>e.word===word);assert(entries.length>=2,word);
 assert.equal(new Set(entries.map(e=>e.details)).size,entries.length,word+' senses have different details');
}
const antenna=details.entries.find(e=>e.word==='ANTENNA'&&e.meaning.includes('アルバム'));
assert.match(antenna.details,/2023年7月5日/);assert.doesNotMatch(antenna.details,/2026年2月18日/);
assert.equal(details.get('みせす','ミセス','英語の敬称。'),null);
assert.equal(details.get(antenna.reading,antenna.word,'別の意味'),null);
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
const context=vm.createContext({ShiritoriMrsDetails:details});context.window=context;
vm.runInContext(html.match(/function parseCSV\([\s\S]*?return Array.from\(map.values\(\)\);\s*}/)[0],context);
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8');
const parsed=vm.runInContext('parseCSV('+JSON.stringify(csv)+')',context);
for(const e of details.entries){
 const r=parsed.find(r=>r.reading===e.reading),i=r.words.findIndex((w,i)=>w===e.word&&r.meanings[i]===e.meaning);
 assert.equal(r.imagequeries[i].source.details,e.details,'CSV fallback: '+e.word);
}
console.log(JSON.stringify({passed:true,senses:207,delivery:true,csvFallback:true,exactSenseKeys:true,originalAlbumDate:true}));
