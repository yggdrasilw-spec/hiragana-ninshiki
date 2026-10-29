const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),items=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-29-oricon1990-2025.review.json'),'utf8'));
const out=path.resolve(root,process.env.SHIRITORI_QA_OUTPUT||'qa-output/oricon');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const f=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html;charset=utf-8':f.endsWith('.js')?'text/javascript':f.endsWith('.json')?'application/json':'text/plain;charset=utf-8'});fs.createReadStream(f).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=process.env.SHIRITORI_QA_ORIGIN||`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'msedge'}),reports=[];
try{for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
 const page=await browser.newPage({viewport}),external=[],requests=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{const u=route.request().url();requests.push(u);if(!u.startsWith(origin)){external.push(u);return route.fulfill({status:200,contentType:'application/json',body:'{}'});}return route.continue();});
 await require('./shiritori-r2-fixture.cjs')(page);
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();});
 assert(!requests.some(u=>/whitelist\.csv|shiritori-grade-policy\.js/.test(u)),'Startup uses the bounded delivery index');
 if(name==='mobile')await page.evaluate(()=>switchMobTab('right'));
 const samples=['1/2','1/3の純情な感情','ラブ・ストーリーは突然に',"B'z",'Mr.Children','SMAP','嵐','Snow Man','SixTONES','乃木坂46','なにわ男子','JO1','INI','櫻井翔','京本大我','池田瑛紗','七五三掛龍也','RYO','HIDE','hide','Doki it','Pieces','永遠に'];
 const longest=items.filter(x=>x.category.startsWith('楽曲')).sort((a,b)=>b.word.length-a.word.length)[0];samples.push(longest.word);
 const networkBefore=external.length;
 for(const word of samples){const x=items.find(x=>x.word===word);assert(x,word);
  await page.evaluate(async x=>{const r=await dictionary.reading(x.reading),i=r.words.findIndex((w,i)=>w===x.word&&r.meanings[i]===x.meaning);if(i<0||r.meaningLevels[i]!==5||r.genres[i]!=='entertainment')throw Error('Missing registered sense '+x.word);await showDetail(x.reading,{...r,words:[r.words[i]],meanings:[r.meanings[i]],meaningLevels:[r.meaningLevels[i]],imagequeries:[r.imagequeries[i]],genres:[r.genres[i]]});clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},x);
  await page.waitForFunction(()=>document.getElementById('detImgBox').textContent.includes('せつめいだけ'));
  assert.equal(await page.locator('.det-word').textContent(),word);assert.equal(await page.locator('#detImgBox img').count(),0);assert((await page.locator('#detContent').textContent()).includes(x.meaning));assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),word);
 }
 assert.equal(external.length,networkBefore,'No external images for the new senses');
 await page.screenshot({path:path.join(out,name+'-long-title.png')});
 const homonyms=[];
 for(const reading of ['はな','あらし','りょう','ひで']){
  const count=await page.evaluate(async reading=>{const r=await dictionary.reading(reading);await showDetail(reading,r);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);return detailView.meanings.length;},reading);assert(count>=2,reading);
  const seen=new Set();for(let i=0;i<count;i++){const w=await page.locator('.det-word').textContent();const m=await page.evaluate(()=>Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join(''));seen.add(w+'\t'+m);await page.locator('#detNext').click();}
  for(const x of items.filter(x=>x.reading===reading))assert(seen.has(x.word+'\t'+x.meaning),'Homonym cycle missed '+x.word+': '+x.meaning);homonyms.push({reading,senses:count});
 }
 if(name==='mobile')await page.evaluate(()=>switchMobTab('center'));
 for(const word of ['1/2','1/3の純情な感情','ラブ・ストーリーは突然に','京本大我','Doki it']){
  const x=items.find(x=>x.word===word);await page.evaluate(()=>{cpuTurn=async()=>{ST.cpuBusy=false;};resetGame();ST.voice=false;ST.level=1;ST.tail='';ST.cpuBusy=false;});
  await page.locator('#linkDraftInput').fill(x.reading);await page.locator('#linkDraftInput').press('Enter');await page.waitForFunction(r=>ST.history.some(x=>x.reading===r),x.reading);
 }
 const n=items.find(x=>x.word==='ロビンソン');assert(n&&n.reading.endsWith('ん'));await page.evaluate(r=>{resetGame();ST.voice=false;ST.tail='';ST.cpuBusy=false;syncInput(r);},n.reading);await page.locator('#btnOk').click();await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);reports.push({viewport:name,detailSamples:samples.length,homonyms,keyboardInputs:5,endingN:true,noExternalDetailRequests:true,passed:true});await page.close();console.log(JSON.stringify({viewport:name,passed:true}));
}fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,reports},null,2)+'\n');}finally{await browser.close();server.closeAllConnections();server.close();}})().catch(e=>{console.error(e);server.closeAllConnections();server.close();process.exitCode=1;});
