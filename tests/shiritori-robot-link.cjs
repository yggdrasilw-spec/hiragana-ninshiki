const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.QA_REPO||path.resolve(__dirname,'..'),out=process.env.QA_OUTPUT||path.join(root,'qa-output/robot-link');
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript','.css':'text/css','.png':'image/png','.json':'application/json','.csv':'text/csv'}[path.extname(file)]||'application/octet-stream'));fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,...(process.env.QA_EXECUTABLE?{executablePath:process.env.QA_EXECUTABLE}:{channel:'chrome'})});
try{for(const [name,width,height]of [['desktop',1280,900],['mobile',390,844],['small',320,720],['tablet',820,900]]){
 const page=await browser.newPage({viewport:{width,height}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();document.querySelectorAll('dialog[open]').forEach(d=>d.close());switchIn('kbd');speakDetail=async()=>{};});
 assert.equal(await page.locator('#colCenter #linkArena').count(),1,'connection is in the main column');
 await page.locator('#kbdInput').fill('りす');assert.equal(await page.evaluate(()=>ST.currentInput),'りす');
 await page.locator('#kbdInput').press('Backspace');assert.equal(await page.evaluate(()=>ST.currentInput),'り');
 await page.locator('#btnBackspace').click();assert.equal(await page.locator('#linkDraftInput').inputValue(),'');
 await page.locator('#tabBtn').click();
 await page.locator('#modeBtn .kb-key').filter({hasText:/^り$/}).click();await page.locator('#modeBtn .kb-key').filter({hasText:/^す$/}).click();
 assert.equal(await page.locator('#linkDraftInput').inputValue(),'りす','button input appears in connection');
 await page.locator('#tabKbd').click();assert.equal(await page.locator('#kbdInput').inputValue(),'りす');
 await page.locator('#kbdInput').fill('');
 await page.evaluate(()=>commitWord('あなた','りんご',lookupRow('りんご')));assert.equal(await page.locator('.rl-bridge').count(),0);
 await page.evaluate(()=>{window.phases=[];window.nextCommit=commitWord('CPU','ごりら',lookupRow('ごりら'));new MutationObserver(()=>{const v=document.querySelector('.rl-bridge')?.dataset.phase;if(v&&window.phases.at(-1)!==v)window.phases.push(v);}).observe(document.getElementById('linkTrack'),{subtree:true,attributes:true,attributeFilter:['data-phase']});});
 await page.waitForFunction(()=>document.querySelector('.rl-bridge')?.dataset.phase==='press');
 const before=await page.locator('.link-node').last().boundingBox();await page.screenshot({path:path.join(out,name+'-press.png')});
 const arena=await page.locator('#linkArena').boundingBox();assert.ok(arena.y>=0&&arena.y+arena.height<=height,'connection animation stays on screen');
 assert.equal(await page.locator('#colCenter').isVisible(),true);assert.equal(await page.locator('#btnOk').innerText(),'つなげる');
 await page.evaluate(()=>window.nextCommit);assert.equal(await page.locator('.rl-bridge').getAttribute('data-phase'),'complete');
 const after=await page.locator('.link-node').last().boundingBox();assert.ok(after.x<before.x-10,'Right block moves toward the fixed left block');
 assert.equal(await page.locator('#linkStatus').innerText(),'「りんご」と「ごりら」が\n「ご」でつながった');
 const phases=await page.evaluate(()=>window.phases);for(const phase of ['grip','press','rotate','lock','pull','complete'])assert.ok(phases.includes(phase),phase);
 assert.equal(await page.evaluate(()=>ST.score.cpu),1);await page.screenshot({path:path.join(out,name+'-complete.png')});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.ok(await page.locator('#kbdInput').isVisible());
 await page.evaluate(()=>renderLinks(true));assert.equal(await page.locator('.rl-bridge').getAttribute('data-phase'),'complete','Same committed pair is not replayed');
 await page.evaluate(()=>{window.pendingCommit=commitWord('あなた','らっぱ',lookupRow('らっぱ'));});await page.waitForFunction(()=>document.querySelector('.rl-bridge:last-of-type')||robotLink.records.size>0);await page.evaluate(()=>resetGame(false));await page.evaluate(()=>window.pendingCommit);await page.waitForTimeout(200);assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>robotLink.records.size),0);assert.equal(await page.evaluate(()=>robotLink.voices.size),0);
 await page.emulateMedia({reducedMotion:'reduce'});await page.evaluate(async()=>{await commitWord('あなた','りんご',lookupRow('りんご'));await commitWord('CPU','ごりら',lookupRow('ごりら'));});assert.equal(await page.locator('.rl-bridge').getAttribute('data-phase'),'complete');await page.emulateMedia({reducedMotion:'no-preference'});
 assert.ok(await page.locator('.sound-credit a[href="https://on-jin.com/"]').count());assert.match(fs.readFileSync(path.join(root,'README.md'),'utf8'),/On-Jin ～音人～/);
 if(name==='desktop'){
  await page.evaluate(()=>{resetGame(false);window.samples=0;const start=AudioBufferSourceNode.prototype.start;AudioBufferSourceNode.prototype.start=function(...args){window.samples++;return start.apply(this,args);};});
  await page.locator('#btnVoice').click();await page.waitForFunction(()=>Object.keys(robotLink.clips).length===8&&robotLink.audio.state==='running');await page.evaluate(()=>commitWord('あなた','りんご',lookupRow('りんご')));await page.evaluate(()=>commitWord('CPU','ごりら',lookupRow('ごりら')));assert.equal(await page.evaluate(()=>window.samples),9);
  await page.locator('#btnVoice').click();assert.equal(await page.evaluate(()=>robotLink.voices.size),0);await page.evaluate(()=>commitWord('あなた','らっぱ',lookupRow('らっぱ')));assert.equal(await page.evaluate(()=>window.samples),9,'OFF suppresses new effects');
 }
 assert.deepEqual(errors,[]);console.log(name,'passed');await page.close();
}console.log(JSON.stringify({passed:true,viewports:4,checks:['stages','right block pulls left','dynamic completion text','scores','reset resolves pending animation','duplicate redraw','reduced motion','sample audio and mute','credit','overflow']}));}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
