const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const policy=require('../shiritori-image-policy.js');
for(const [word,meaning,category] of [['犬','人と暮らす動物。','animal'],['柿','甘い果物。','plant'],['牡蠣','海にすむ二枚貝。','animal'],['書き','文字を書くこと。','other'],['キノコ','かさのある菌類。','fungi'],['アイアント','鉄を食べるアリポケモン','other']])assert.equal(policy.category(word,meaning),category);
assert.equal(policy.source({default:'wikimedia',categories:{animal:'asset'}},'animal'),'asset');
assert.equal(policy.source({default:'wikimedia'},'plant'),'wikimedia');
assert.equal(policy.normalize({default:'bad'}).default,'asset');
const html=fs.readFileSync(require('node:path').join(__dirname,'../shiritori.html'),'utf8');
let searches=0;
class Image{set src(value){queueMicrotask(()=>{this.naturalWidth=100;this.onload();});}}
const box=vm.createContext({ST:{imagePolicy:policy.normalize(null)},ShiritoriImagePolicy:policy,Image,URL,AbortController,setTimeout,clearTimeout,escH:s=>s,console,fetch:async()=>({ok:true,json:async()=>({})})});
vm.runInContext(html.slice(html.indexOf('const IMG_CACHE ='),html.indexOf('let detailView =')),box);
box.search=()=>{searches++;return 'https://upload.wikimedia.org/test.jpg';};
vm.runInContext('fetchPageImage=async()=>search();checkImgCredit=async()=>({ok:true,credit:{text:"Wikimedia / photographer / CC BY-SA 4.0"}})',box);
(async()=>{
 const q="{ja:'犬',asset:'assets/shiritori/common-word-398.png',mode:'asset',category:'animal'}";
 assert.equal((await vm.runInContext('fetchImg('+q+')',box)).url,'./assets/shiritori/common-word-398.png');assert.equal(searches,0);
 box.ST.imagePolicy.categories.animal='wikimedia';
 assert.equal((await vm.runInContext('fetchImg('+q+')',box)).url,'https://upload.wikimedia.org/test.jpg');assert.equal(searches,1);
 box.ST.imagePolicy.categories.animal='asset';
 assert.equal((await vm.runInContext('fetchImg('+q+')',box)).url,'./assets/shiritori/common-word-398.png');
 box.ST.imagePolicy.categories.animal='wikimedia';vm.runInContext('IMG_CACHE.clear();fetchPageImage=fetchPageImageBySearch=fetchCommonsByTitle=fetchCommonsByFulltext=async()=>null',box);
 const fallback=await vm.runInContext('fetchImg('+q+')',box);assert.match(fallback.credit.text,/見つからない/);assert.match(fallback.url,/common-word-398/);
 const counts={};for(const line of fs.readFileSync(require('node:path').join(__dirname,'../whitelist.csv'),'utf8').trim().split(/\r?\n/).slice(1)){const c=line.split(','),kind=policy.category(c[1],c[2],c[3]);counts[kind]=(counts[kind]||0)+1;}
 console.log(JSON.stringify({passed:true,counts,checks:['homophones','fiction exclusion','inheritance','asset avoids search','wikimedia bypasses stored asset','cache varies by source','fallback credit']}));
})().catch(e=>{console.error(e);process.exitCode=1;});
