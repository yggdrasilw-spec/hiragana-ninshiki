const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/ux');
const server=http.createServer((req,res)=>{const file=path.join(root,decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}res.setHeader('Content-Type',path.extname(file)==='.html'?'text/html; charset=utf-8':'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
 const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844],['small',320,640],['tablet',820,700]]){
 const page=await browser.newPage({viewport:{width,height}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.emulateMedia({reducedMotion:'reduce'});
 assert.equal(await page.evaluate(()=>{ST.voice=false;return getCpuDelay({words:['a','b'],meanings:['x'.repeat(1000)]});}),650,'Mute delay does not grow with meaning length');
 await page.evaluate(async()=>{ST.voice=false;await launchGame();switchIn('kbd');getCpuDelay=()=>80;});
 assert.equal(await page.locator('#titleScreen').count(),0,'Reduced motion still starts the game');
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.locator('#kbdInput').fill('りす');await page.locator('#btnOk').click();
 await page.waitForFunction(()=>ST.history.length===2&&!ST.cpuBusy);
 assert.equal(await page.locator('.link-node').count(),2);assert.match(await page.locator('#linkCount').innerText(),/1/);
 if(width<=768)assert.ok(await page.locator('#colCenter').isVisible(),'Do not switch tabs after commit');
 assert.ok(await page.locator('#linkStatus').innerText(),'Status visible beside input');
 await page.screenshot({path:path.join(out,name+'.png'),fullPage:true});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');
 assert.ok(await page.locator('#kbdInput').isVisible());
 await page.evaluate(async()=>{resetGame();await commitWord('あなた','しりとり',lookupRow('しりとり'));await commitWord('CPU','りす',lookupRow('りす'));await commitWord('あなた','すいか',lookupRow('すいか'));await commitWord('CPU','かめ',lookupRow('かめ'));});
 await page.screenshot({path:path.join(out,name+'-chain.png'),fullPage:true});
 // Restart during the pending CPU turn must leave the new round empty.
 await page.evaluate(()=>{resetGame();setCurrentInput('りす');submitWord();});await page.waitForFunction(()=>ST.history.length===1);
 await page.evaluate(()=>resetGame());await page.waitForTimeout(850);
 assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.cpuBusy),false);
 // Sampling covers the whole candidate pool, including entries beyond the old first six.
 assert.equal(await page.evaluate(()=>{
   resetGame();ST.tail='は';ST.cpuAllowN=false;
   const pool=getPool().filter(r=>!isEndWord(r.reading)&&firstChar(r.reading)==='は');
   const random=Math.random;
   try{Math.random=()=>0.999999;return cpuChoose()===pool[pool.length-1];}finally{Math.random=random;}
 }),true);
 // A speech implementation that never emits end/error must still release the turn.
 await page.evaluate(async()=>{
   const original=window.speechSynthesis;
   Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{cancel(){},speak(){}}});
   try{
     ST.voice=true;
     const start=performance.now();await speakAsync('テスト',40);
     if(performance.now()-start>1000)throw new Error('Speech watchdog did not release');
     const pending=speakAsync('リセット待ち',10000);resetGame(false);await pending;
     if(finishSpeech!==null)throw new Error('Reset leaves pending speech');
   }finally{Object.defineProperty(window,'speechSynthesis',{configurable:true,value:original});ST.voice=false;}
 });
 await page.evaluate(async()=>{resetGame();await showEndGameByN('みかん',lookupRow('みかん'));});
 await page.waitForFunction(()=>ST.replayOverlayOpen);
 assert.equal(await page.evaluate(()=>document.body.classList.contains('panic')),false,'Player ending remains calm');
 assert.match(await page.locator('#scMain').innerText(),/ここまでつながった/);
 await page.waitForTimeout(220);
 await page.screenshot({path:path.join(out,name+'-calm-ending.png'),fullPage:true});
 await page.evaluate(()=>resetGame());
 // Enter that confirms an IME composition must not submit a word.
 await page.locator('#kbdInput').fill('りす');await page.locator('#kbdInput').dispatchEvent('keydown',{key:'Enter',isComposing:true});
 assert.equal(await page.evaluate(()=>ST.history.length),0);
 // Unavailable word validation must not silently learn a fabricated word.
 await page.evaluate(async()=>{ST.gasUrl='';setCurrentInput('あああああああ');await submitWord();});
 assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.whitelist.some(r=>r.reading==='あああああああ')),false);
 assert.equal(await page.evaluate(()=>!!safeParseAIResult('{}','りす')._fallback),true,'Malformed AI response is unverified');
 assert.equal(await page.evaluate(()=>safeParseAIResult('{"valid":false}','りす').ok),false);
 assert.equal(await page.evaluate(()=>{emergencyAudioCtx=null;ST.voice=false;playEmergencyBuzzer();return emergencyAudioCtx;}),null,'Mute applies to the ending buzzer');
 await page.evaluate(()=>{resetGame();switchIn('btn');});
 await page.screenshot({path:path.join(out,name+'-buttons.png'),fullPage:true});
 await page.evaluate(()=>switchIn('canvas'));
 assert.ok(await page.locator('#drawCanvas').isVisible());
 if(width<=768)assert.ok(await page.locator('#colCenter .panel').evaluate(e=>e.getBoundingClientRect().height>=300),'Drawing panel retains room for controls');
 await page.screenshot({path:path.join(out,name+'-canvas.png'),fullPage:true});
 // A CPU with no valid reply ends the game exactly once.
 await page.evaluate(async()=>{resetGame();ST.tail='り';cpuChoose=()=>null;await cpuTurn();});
 assert.equal(await page.evaluate(()=>ST.gameOver),true);assert.ok(await page.locator('#replayOverlay').isVisible());
 await page.evaluate(async()=>{resetGame();ST.tail='み';cpuChoose=()=>lookupRow('みかん');await cpuTurn();});
 assert.equal(await page.evaluate(()=>ST.gameOver),true);assert.equal(await page.evaluate(()=>document.body.classList.contains('panic')),false,'A CPU loss celebrates instead of alarming');
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('#linkArena').evaluate(e=>getComputedStyle(e).animationName),'none');
 assert.deepEqual(errors,[]);await page.close();
 }
 console.log(JSON.stringify({passed:true,viewports:4,checks:['chain','reset race','IME','offline and malformed validation','CPU win','reduced motion launch','mute','three input modes','overflow','fixed mute delay','whole CPU pool','speech watchdog and reset','calm ending'],out}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
