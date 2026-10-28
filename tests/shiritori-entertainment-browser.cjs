const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-28-entertainment');
const items=JSON.parse(fs.readFileSync(base+'.review.json','utf8')),out=path.join(root,'qa-output/entertainment');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const f=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript':f.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(f).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
try{for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
 const page=await browser.newPage({viewport}),external=[],requests=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{const u=route.request().url();requests.push(u);if(!u.startsWith(origin)){external.push(u);return route.fulfill({status:200,contentType:'application/json',body:'{}'});}return route.continue();});
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});await page.locator('#noticeStart').click();
 assert(!requests.some(u=>/whitelist\.csv|shiritori-grade-policy\.js/.test(u)),'No complete dictionary download on startup');
 const all=await page.evaluate(async items=>{
  ST.voice=false;ST.level=5;ST.imagePolicy={default:'wikimedia',categories:{}};let valid=0,blank=0;
  for(const x of items){if(inWhitelist(x.reading))valid++;const r=await dictionary.reading(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);if(i<0)throw Error('Missing '+x.word);if(r.genres[i]!=='entertainment'||r.meaningLevels[i]!==5)throw Error('Wrong genre/level '+x.word);const img=await fetchImg(r.imagequeries[i]);if(img.url===null)blank++;}
  return {valid,blank};
 },items);assert.deepEqual(all,{valid:items.length,blank:items.length});
 const counts=await page.evaluate(()=>[1,2,3,4,5].map(l=>dictionary.count(l,['entertainment'])));assert(counts[4]>=new Set(items.map(x=>x.reading)).size);assert.equal(counts[0],0);
 const networkBefore=external.length;
 const names=['Mrs. GREEN APPLE','大森元貴','ライラック','シンデレラ','0.2mm','French','POPS','ゼンジン未到とイ/ミュータブル～間奏編～','明石家さんま','ダウンタウン','千と千尋の神隠し','ミュージックステーション'];
 if(name==='mobile')await page.evaluate(()=>switchMobTab('right'));
 for(const word of names){const x=items.find(x=>x.word===word);assert(x,word);await page.evaluate(async x=>{const r=await dictionary.reading(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);await showDetail(x.reading,{...r,words:[r.words[i]],meanings:[r.meanings[i]],meaningLevels:[r.meaningLevels[i]],imagequeries:[r.imagequeries[i]],genres:[r.genres[i]]});clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},x);
  await page.waitForFunction(()=>document.getElementById('detImgBox').textContent.includes('せつめいだけ'));
  assert.equal(await page.locator('#detImgBox img').count(),0);assert.equal(await page.locator('.det-word').textContent(),word);assert((await page.locator('#detContent').textContent()).includes(x.meaning.split('。')[0]));
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),word);
  if(['大森元貴','ゼンジン未到とイ/ミュータブル～間奏編～'].includes(word))await page.screenshot({path:path.join(out,name+'-'+(word==='大森元貴'?'ohmori':'live')+'.png')});
 }
 assert.equal(external.length,networkBefore,'No external searches for explanation-only entries');
 const homophones=await page.evaluate(async()=>{const r=await dictionary.reading('ふれんち');await showDetail(r.reading,r);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);return detailView.meanings.length;});assert.equal(homophones,2);const first=await page.locator('.det-summary').innerText();await page.locator('#detNext').click();assert.notEqual(await page.locator('.det-summary').innerText(),first);
 if(name==='mobile')await page.evaluate(()=>switchMobTab('center'));
 await page.evaluate(()=>{resetGame();ST.voice=false;ST.level=1;cpuTurn=async()=>{ST.cpuBusy=false;};});
 await page.locator('#linkDraftInput').fill('おおもりもとき');await page.locator('#linkDraftInput').press('Enter');await page.waitForFunction(()=>ST.history.some(x=>x.reading==='おおもりもとき'));
 await page.evaluate(()=>{resetGame();ST.voice=false;syncInput('なんばーせぶん');});await page.locator('#btnOk').click();await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);reports.push({viewport:name,registered:all.valid,noImageResults:all.blank,detailSamples:names.length,homophones,genreCounts:counts,keyboardInputAtLevel1:true,endingN:true,noExternalDetailRequests:true,passed:true});await page.close();console.log(JSON.stringify({viewport:name,passed:true}));
}fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,reports},null,2)+'\n');}finally{await browser.close();server.closeAllConnections();server.close();}})().catch(e=>{console.error(e);server.closeAllConnections();server.close();process.exitCode=1;});
