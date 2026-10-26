const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),json=p=>JSON.parse(read(p)),sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const base='data/dictionary-imports/2026-10-25-seven-categories1024',initial='data/dictionary-imports/2026-10-25-seven-categories';
const first=json(initial+'.review.json'),next=json(base+'.review.json'),all=[...first,...next],summary=json(base+'.summary.json');
assert.equal(first.length,149);assert.equal(next.length,875);assert.equal(all.length,1024);assert.equal(summary.registered,true);
const csv=read('whitelist.csv'),lines=csv.trimEnd().split(/\r?\n/),header=lines[0].split(','),rows=lines.slice(1).map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
assert.equal(rows.length,16574);const history=json('data/dictionary-imports/history.json');assert.equal(sha(csv),history.at(-1).afterSha256);assert.ok(history.some(x=>x.afterSha256===summary.afterSha256&&x.addedLines?.length===875));
const imagePlans=['seven512','seven512b'].map(batch=>json('data/image-coverage/2026-10-25-'+batch+'-images/plan.json').items);assert.equal(imagePlans[0].length,512);assert.equal(imagePlans[1].length,512);const illustrated=new Map(imagePlans.flat().map(x=>[x.id,'assets/shiritori/'+x.filename]));assert.equal(illustrated.size,1024);assert.deepEqual(new Set(illustrated.keys()),new Set(all.map(x=>x.id)));
// The entire dictionary before this user's addition remains byte-identical.
const baseline=lines.slice(0,15551).join('\n')+'\n';assert.equal(sha(baseline),json(initial+'.summary.json').beforeSha256);
assert.equal(new Set(all.map(x=>[x.reading,x.word,x.meaning].join('\t'))).size,1024);
const grades=json('data/shiritori-grade-review.json'),coverage=json('data/image-coverage/review-2026-10-10.json'),updates=json('data/image-coverage/review-updates.json');
assert.equal(grades.length,rows.length);assert.equal(coverage.length,rows.length);assert.equal(updates.entries.length,rows.length);assert.equal(updates.csvSha256,sha(csv));
for(const x of all){
 const row=rows[x.id-1];for(const k of ['reading','word','meaning'])assert.equal(row[k],x[k]);
 assert.equal(row.image_mode,illustrated.has(x.id)?'asset':'none');assert.equal(row.image_asset,illustrated.get(x.id)||'');assert.equal(grades[x.id-1].level,x.grade);
 assert.deepEqual(updates.entries[x.id-1].text,[x.reading,x.word,x.meaning]);assert.equal(coverage[x.id-1].status,illustrated.has(x.id)?'covered':'explanation-only');
 assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason);
}
assert.equal(history.at(-1).afterSha256,sha(csv));assert.equal(history.find(x=>x.afterSha256===summary.afterSha256).addedLines.length,875);
assert.deepEqual(all.reduce((out,x)=>(out[x.category]=(out[x.category]||0)+1,out),{}),{sumo:82,judo:100,karate:53,pokemon:366,koji:89,proverb:130,compound:204});
const lexical=json(base+'.lexical-checks.json');assert.equal(lexical.officialSumoCount,82);assert.equal(lexical.martial.filter(x=>x.category==='judo'&&x.verified).length,100);
const get=r=>all.find(x=>x.reading===r&&x.category==='pokemon');
assert.match(get('へんしん').meaning,/変身/);assert.match(get('いたみわけ').meaning,/平均/);assert.match(get('すけっち').meaning,/ずっと自分の技/);assert.match(get('ねごと').meaning,/眠っている/);assert.match(get('みちづれ').meaning,/相手もひんし/);
assert.equal(all.find(x=>x.word==='掌底打ち').reading,'しょうていうち');assert.equal(all.find(x=>x.word==='掌底受け').reading,'しょうていうけ');
console.log(JSON.stringify({passed:true,totalAdded:all.length,totalRows:rows.length,originalRowsPreserved:15550,meaningLevels:true,sourceLinks:true,pokemonEffectMappings:true}));
