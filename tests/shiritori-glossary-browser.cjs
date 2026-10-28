const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),items=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-28-glossary.review.json'),'utf8'));
const out=path.join(root,'qa-output/glossary');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});server.keepAliveTimeout=1;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>requests.push(r.url()));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);ST.showHints=false;document.getElementById('titleScreen')?.remove();switchIn('kbd');});if(width<769)await page.locator('#mobTabRight').click();
 assert.ok(!requests.some(u=>/whitelist\.csv|shiritori-grade-policy\.js/.test(u)),'No full source download');
 const ordered=[...items].sort((a,b)=>a.reading<b.reading?-1:a.reading>b.reading?1:a.id-b.id),levels=[0,0,0,0,0];
 for(let offset=0;offset<ordered.length;offset+=75){
  const counts=await page.evaluate(async batch=>{const counts=[0,0,0,0,0];for(const x of batch){const row=await dictionary.reading(x.reading),i=row?.meanings.findIndex((m,j)=>m===x.meaning&&row.words[j]===x.word);if(i===undefined||i<0||row.meaningLevels[i]!==5)throw Error('Missing sense '+x.id+' '+x.word);
   for(let l=1;l<=5;l++){ST.level=l;ST.tail=firstChar(x.reading);const pool=getPool([row]);if(pool.some(r=>r.words.some((w,i)=>w===x.word&&r.meanings[i]===x.meaning)))counts[l-1]++;}ST.level=5;
   const selected={...row,words:[row.words[i]],meanings:[row.meanings[i]],meaningLevels:[5],imagequeries:[row.imagequeries[i]],genres:[row.genres[i]]};await showDetail(x.reading,selected);await new Promise(r=>setTimeout(r,0));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
   const text=Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join('');if(document.querySelector('.det-word')?.textContent!==x.word||text!==x.meaning)throw Error('Wrong rendered text '+x.id+' '+x.word);
   if(document.querySelector('#detImgBox .img-main')||!document.querySelector('#detImgBox')?.textContent.includes('せつめいだけ'))throw Error('Wrong image mode '+x.word);
   if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal overflow '+x.word);
  }return counts;},ordered.slice(offset,offset+75));counts.forEach((n,i)=>levels[i]+=n);
  if(offset%600===0)console.log(JSON.stringify({width,checked:Math.min(offset+75,ordered.length),total:ordered.length}));
 }
 assert.deepEqual(levels,[0,0,0,0,items.length]);
 const homonyms=[];for(const reading of ['ぱーす','ぶーばー','あっしゅ','こすもす','かおす','こっか']){
  await page.evaluate(async r=>{ST.level=5;await showDetail(r,await dictionary.reading(r));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
  const count=await page.evaluate(()=>detailView.meanings.length),seen=[];assert.ok(count>=2,reading);for(let i=0;i<count;i++){seen.push(await page.locator('.det-word').innerText()+'\t'+await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}assert.equal(new Set(seen).size,count);homonyms.push({reading,senses:count});
 }
 await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
 const inputs=['たれす','いまぬえるかんと','かんと','みる','じぇーえすみる','りゅうじゅ','なーがーるじゅな','はんなあれんと','あじきなし','はずれち','あいぴーあどれす'];
 for(const r of inputs){assert.ok(await page.evaluate(r=>inWhitelist(r),r),r);await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(r==='かんと'?'カント':r);await page.locator('#kbdInput').press('Enter');await page.waitForFunction(r=>ST.used.has(norm(r)),r);await page.waitForFunction(()=>!ST.cpuBusy);}
 if(width<769)await page.locator('#mobTabRight').click();await page.evaluate(async()=>{await showDetail('いまぬえるかんと',await dictionary.reading('いまぬえるかんと'));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);});await page.screenshot({path:path.join(out,'kant-'+width+'.png')});
 if(width<769)await page.locator('#mobTabCenter').click();await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill('ぷらとーん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);results.push({width,meanings:items.length,levels,homonyms,keyboardInputs:inputs.length,endingN:true,errors});await page.close();console.log(JSON.stringify({width,passed:true}));
}fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,results},null,2)+'\n');}finally{server.closeAllConnections();await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;server.closeAllConnections();server.close();});
