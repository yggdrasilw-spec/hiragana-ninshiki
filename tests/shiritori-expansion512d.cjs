const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),name='2026-10-15-expansion512d';
const json=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const summary=json('data/image-coverage/'+name+'/summary.json'),plan=json('data/image-coverage/'+name+'/plan.json');
const review=json('data/dictionary-imports/'+name+'.review.json');
const source=json('data/dictionary-imports/'+name+'.source.json');
const lines=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trimEnd().split(/\r?\n/),header=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
assert.equal(review.length,512);assert.equal(source.rows.length,512);assert.equal(new Set(review.map(x=>x.reading)).size,512);
const before=header.join(',')+'\n'+lines.slice(0,summary.baselineRows).join('\n')+'\n';
assert.equal(crypto.createHash('sha256').update(before).digest('hex'),summary.beforeSha256,'Preserve preceding vocabulary, IDs, explanations and images');
const old=new Set(rows.slice(0,summary.baselineRows).map(x=>x.reading));
const reserved=new Set(json('data/image-coverage/'+name+'/reservation-snapshot.json').readings);
const concurrent=json('data/image-coverage/2026-10-15-expansion512c/plan.json').items;
const other=new Set(concurrent.map(x=>x.reading));
const manifest=json('assets/shiritori/manifest.json');
const assets=new Map(manifest.assets.map(x=>[x.file,x]));assert.equal(assets.size,manifest.assets.length);
for(const x of review){
 const row=rows[x.id-1];
 assert.ok(!old.has(x.reading)&&!reserved.has(x.reading)&&!other.has(x.reading),'Independent new reading: '+x.reading);
 assert.match(x.reading,/^[ぁ-ゖー]+$/);
 for(const k of ['reading','word','meaning'])assert.equal(row[k],x[k]);
 assert.equal(Number(row.level),x.level);assert.equal(row.image_mode,'asset');assert.equal(row.image_credit,x.credit);
 assert.equal(row.image_asset,'assets/shiritori/'+x.filename);
 assert.ok(x.lexicalSource&&x.meaningReason&&x.ageReason&&x.imageReason);
 const a=assets.get(x.filename);assert.ok(a?.aliases.some(y=>y.id===x.id&&y.reading===x.reading&&y.meaning===x.meaning));
 const b=fs.readFileSync(path.join(root,row.image_asset));assert.equal(b.readUInt32BE(16),256);assert.equal(b.readUInt32BE(20),256);
 if(x.sourceRecord){const r=x.sourceRecord;assert.equal(x.reading,r.familynamekana+r.fisrtnamekana,'Official athlete reading');}
}
assert.equal(review.filter(x=>x.credit==='独自文字カード（外部検索なし）').length,352);
assert.equal(review.filter(x=>x.credit==='AI生成イラスト').length,160);
assert.equal(review.find(x=>x.word==='山縣亮太').reading,'やまがたりょうた');
assert.equal(review.find(x=>x.word==='赤間凛音').reading,'あかまりず');
assert.equal(review.find(x=>x.word==='松島輝空').reading,'まつしまそら');
assert.ok(review.find(x=>x.word==='イタリアンスパゲッティ').meaning.includes('名古屋'));
assert.ok(!review.find(x=>x.word==='イタリアンスパゲッティ').meaning.includes('新潟'));
assert.ok(!review.some(x=>x.word==='モルフォナイト'));assert.ok(review.some(x=>x.word==='バルフレイナイト'));
// The failure path is as important as the successful-card path: a missing local
// file must never trigger a portrait/logo/character image search.
const html=fs.readFileSync(path.join(root,'shiritori.html'),'utf8');
for(const script of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(script[1]);
const images=html.slice(html.indexOf('const IMG_CACHE ='),html.indexOf('async function showDetail('));
const ctx=vm.createContext({ShiritoriAssets:require('../shiritori-assets.js'),URL,Image:class{},AbortController,setTimeout,clearTimeout,ST:{imagePolicy:{}},ShiritoriImagePolicy:{source:()=> 'wikimedia'},available:true,searches:0});
vm.runInContext(images,ctx);
vm.runInContext("canLoadImage=async()=>available; fetchPageImage=fetchPageImageBySearch=fetchCommonsByTitle=fetchCommonsByFulltext=async()=>{searches++;return null;};",ctx);
(async()=>{
 for(const source of ['asset','wikimedia']){
  ctx.ShiritoriImagePolicy.source=()=>source;
  ctx.available=true;
  const found=await vm.runInContext("fetchImg({ja:'大谷翔平',asset:'assets/shiritori/test-card.png',mode:'asset',credit:'独自文字カード（外部検索なし）'})",ctx);
  assert.equal(found.url,'https://shiritori-images.yggdrasil-learning.workers.dev/assets/shiritori/test-card.png');assert.equal(ctx.searches,0);
  ctx.available=false;
  const missing=await vm.runInContext("fetchImg({ja:'大谷翔平',asset:'assets/shiritori/missing-card.png',credit:'独自文字カード（外部検索なし）'})",ctx);
  assert.equal(missing.url,null);assert.equal(ctx.searches,0);
 }
 await vm.runInContext("fetchImg({ja:'普通の料理'})",ctx);assert.ok(ctx.searches>0,'Control confirms the search instrumentation is active');
 console.log(JSON.stringify({passed:true,newWords:512,illustrations:160,textCards:352,overlap:0,priorRowsPreserved:summary.baselineRows,noExternalSearch:true,missingCardNoSearch:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
