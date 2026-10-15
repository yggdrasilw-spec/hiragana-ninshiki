// A deliberate no-image sense must bypass every source, asset and cache path.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../shiritori.html'),'utf8');
for(const s of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(s[1]);
const parser=html.slice(html.indexOf('function parseCSV('),html.indexOf('const ST ='));
const images=html.slice(html.indexOf('const IMG_CACHE ='),html.indexOf('async function showDetail('));
const ctx=vm.createContext({URL,Image:class{},AbortController,setTimeout,clearTimeout,escH:String,ST:{imagePolicy:{}},ShiritoriImagePolicy:{source:()=> 'wikimedia',category:()=> 'other'},calls:0});
vm.runInContext(parser+images,ctx);
vm.runInContext("canLoadImage=fetchPageImage=fetchPageImageBySearch=fetchCommonsByTitle=fetchCommonsByFulltext=async()=>{calls++;throw Error('No image I/O allowed');};",ctx);
(async()=>{
 ctx.csv='reading,word,meaning,imagequery,level,imagequery_en,image_asset,image_mode,image_credit\nたい,鯛,海の魚。,鯛,1,,,,\nたい,タイ,商品名のテスト。,タイ,3,,,none,説明のみ\n';
 const groups=vm.runInContext('parseCSV(csv)',ctx);assert.equal(groups.length,1);
 assert.equal(groups[0].imagequeries[0].mode,'fallback');assert.equal(groups[0].imagequeries[1].mode,'none','Homophones retain separate image rules');
 for(const mode of ['asset','wikimedia']){
  ctx.ShiritoriImagePolicy.source=()=>mode;
  for(const asset of [null,'assets/shiritori/old.png','https://example.com/logo.png']){
   ctx.query={ja:'コカ・コーラ',en:'Coca-Cola',mode:'none',asset};
   const r=await vm.runInContext('fetchImg(query)',ctx);assert.equal(r.url,null);assert.match(r.credit.text,/説明のみ/);
   assert.match(vm.runInContext('renderImgHtml(null,{text:"このことばは説明のみです（画像は表示しません）"})',ctx),/せつめいだけ/);
  }
 }
 assert.equal(ctx.calls,0);console.log(JSON.stringify({passed:true,noImageIO:true,sourcePreferenceBypass:true,perSense:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
