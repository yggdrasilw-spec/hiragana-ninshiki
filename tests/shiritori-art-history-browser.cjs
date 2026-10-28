const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),base=path.join(root,'data/dictionary-imports/2026-10-28-art-history'),items=JSON.parse(fs.readFileSync(base+'.final-review.json','utf8'));
const out=path.join(root,'qa-output/art-history');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const f=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!f.startsWith(root+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404);return res.end();}res.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html; charset=utf-8':f.endsWith('.js')?'text/javascript':f.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(f).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[],external=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>{if(r.request().url().startsWith(origin))return r.continue();external.push(r.request().url());return r.fulfill({status:200,contentType:'application/json',body:'{}'});});await require('./shiritori-r2-fixture.cjs')(page);
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);});if(width<769)await page.locator('#mobTabRight').click();
 const pools=await page.evaluate(async items=>{
  const groups=new Map(),counts=[0,0,0,0,0];for(const x of items){const h=firstChar(x.reading);if(!groups.has(h))groups.set(h,[]);groups.get(h).push(x);}
  for(const [head,list] of groups){const prepared=await dictionary.prepare(head,5,ST.cpuGenres);ST.tail=head;for(let level=1;level<=5;level++){ST.level=level;const pool=getPool(prepared);counts[level-1]+=list.filter(x=>pool.some(r=>r.reading===x.reading&&r.meanings.includes(x.meaning))).length;}}
  ST.tail='';ST.level=5;return counts;
 },items);assert.deepEqual(pools,[0,0,0,0,items.length]);
 const before=external.length,sorted=[...items].sort((a,b)=>a.reading.localeCompare(b.reading));
 for(let offset=0;offset<sorted.length;offset+=80)await page.evaluate(async list=>{for(const x of list){
  const row=await dictionary.reading(x.reading),index=row?.meanings.findIndex((m,i)=>m===x.meaning&&row.words[i]===x.word);if(index===undefined||index<0||row.meaningLevels[index]!==5)throw Error('Missing sense: '+x.word);
  const selected=ShiritoriVocabulary.project(row,[index]);await showDetail(x.reading,selected);await new Promise(r=>setTimeout(r,0));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
  const text=Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join('');if(document.querySelector('.det-word')?.textContent!==x.word||text!==x.meaning)throw Error('Wrong detail: '+x.word);
  if(document.querySelector('#detImgBox img')||!document.querySelector('#detImgBox')?.textContent.includes('せつめいだけ'))throw Error('Wrong image mode: '+x.word);
  if(document.documentElement.scrollWidth>innerWidth)throw Error('Overflow: '+x.word);
 }},sorted.slice(offset,offset+80));assert.equal(external.length,before,'No external image searches for the new senses');
 const homonyms=[];for(const reading of ['せっぷん','じゅたいこくち']){
  await page.evaluate(async reading=>{await showDetail(reading,await dictionary.reading(reading));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
  const count=await page.evaluate(()=>detailView.meanings.length),seen=[];assert.ok(count>=2,reading);for(let i=0;i<count;i++){seen.push(await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}assert.equal(new Set(seen).size,count);homonyms.push({reading,senses:count});
 }
 await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
 const words=['星月夜','印象派','神奈川沖浪裏','スフマート','アール・デコ'];
 for(const word of words){const x=items.find(x=>x.word===word);assert.ok(x,word);await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(x.reading);await page.locator('#kbdInput').press('Enter');await page.waitForFunction(r=>ST.used.has(norm(r)),x.reading);await page.waitForFunction(()=>!ST.cpuBusy);}
 if(width<769)await page.locator('#mobTabRight').click();await page.evaluate(async()=>{await showDetail('ほしづきよ',await dictionary.reading('ほしづきよ'));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);});await page.screenshot({path:path.join(out,'starry-night-'+width+'.png')});
 if(width<769)await page.locator('#mobTabCenter').click();await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill('でざいん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);results.push({width,meanings:items.length,pools,homonyms,keyboardInputs:words.length,endingN:true,noExternalDetailSearch:true,errors});await page.close();console.log(JSON.stringify({width,passed:true}));
}const result={passed:true,results};fs.writeFileSync(path.join(out,'result.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(base+'.validation.json',JSON.stringify(result,null,2)+'\n');}finally{server.closeAllConnections();await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;server.closeAllConnections();server.close();});
