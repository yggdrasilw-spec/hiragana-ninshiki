const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),fallback=process.env.SCIENCE_TEST_FALLBACK||root;
const items=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-28-science.review.json'),'utf8'));
const out=path.join(root,'qa-output/science');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const relative=decodeURIComponent(new URL(req.url,'http://localhost').pathname).replace(/^\//,'');let file=path.resolve(root,relative);if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}if(!fs.existsSync(file))file=path.resolve(fallback,relative);if(!file.startsWith(fallback+path.sep)&&!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));await require('./shiritori-r2-fixture.cjs')(page);
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});if(width<769)await page.locator('#mobTabRight').click();
 for(let offset=0;offset<items.length;offset+=100){
  await page.evaluate(async batch=>{for(const x of batch){const row=await dictionary.reading(x.reading),i=row.words.findIndex((w,j)=>w===x.word&&row.meanings[j]===x.meaning);if(i<0||row.meaningLevels[i]!==5||row.genres[i]!==x.genre)throw Error('Wrong sense/grade/genre '+x.word);
   await showDetail(x.reading,{...row,words:[row.words[i]],meanings:[row.meanings[i]],meaningLevels:[5],imagequeries:[row.imagequeries[i]]});clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);await new Promise(r=>setTimeout(r,0));
   const displayed=Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join('');if(document.querySelector('.det-word')?.textContent!==x.word||displayed!==x.meaning)throw Error('Wrong detail '+x.word);
   if(!Array.from(document.querySelectorAll('#detContent a')).some(a=>a.href===x.source.url))throw Error('Missing attribution '+x.word);
   if(document.querySelector('#detImgBox .img-main')||!document.getElementById('detImgBox').textContent.includes('せつめいだけ'))throw Error('Wrong image mode '+x.word);
   if(document.documentElement.scrollWidth>innerWidth)throw Error('Overflow '+x.word);
  }},items.slice(offset,offset+100));
  if(offset%1000===0)console.log(JSON.stringify({width,checked:Math.min(offset+100,items.length)}));
 }
 const genres=await page.evaluate(()=>['chemistry','physics','biology','earthScience'].map(genre=>({genre,elementary:dictionary.count(4,[genre]),advanced:dictionary.count(5,[genre])})));assert.ok(genres.every(g=>g.elementary===0&&g.advanced>900));
 for(const word of ['仕事','卵割','硝化','光束']){const x=items.find(i=>i.word===word);await page.evaluate(async x=>{const row=await dictionary.reading(x.reading),i=row.meanings.indexOf(x.meaning);await showDetail(x.reading,{...row,words:[row.words[i]],meanings:[row.meanings[i]],meaningLevels:[5],imagequeries:[row.imagequeries[i]]});clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},x);await page.screenshot({path:path.join(out,word+'-'+width+'.png')});}
 if(width<769)await page.locator('#mobTabCenter').click();await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});await page.locator('#tabKbd').click();
 for(const word of ['卵割','クーロンの法則','解糖系','プレートテクトニクス']){const x=items.find(i=>i.word===word);assert.ok(x,word);await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(x.reading);await page.locator('#kbdInput').press('Enter');await page.waitForFunction(r=>ST.used.has(norm(r)),x.reading);}
 assert.deepEqual(errors,[]);results.push({width,meanings:items.length,genres,inputs:4,errors});await page.close();console.log(JSON.stringify({width,passed:true}));
}fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,results},null,2)+'\n');}finally{server.closeAllConnections();await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;server.closeAllConnections();server.close();});
