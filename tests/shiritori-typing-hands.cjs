const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/typing-hands');
const server=http.createServer((req,res)=>{
 const file=path.join(root,decodeURIComponent(req.url.split('?')[0]));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[path.extname(file)]||'application/octet-stream'));fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
 const origin=process.env.QA_BASE_URL||`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({channel:'chrome',headless:true});
 try{
 for(const [width,height]of [[1280,900],[390,844],[320,740],[844,390]]){
  const page=await browser.newPage({viewport:{width,height}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  if(!process.env.QA_BASE_URL){
   await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
   await require('./shiritori-r2-fixture.cjs')(page);
  }
  await page.goto(origin+'/shiritori.html'+(process.env.QA_CACHE_KEY?'?guide='+encodeURIComponent(process.env.QA_CACHE_KEY):''));await page.waitForFunction(()=>ST.wlLoaded);
  await page.locator('#noticeStart').click();
  await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();ST.voice=false;switchIn('kbd');});
  await page.emulateMedia({reducedMotion:'no-preference'});
  async function pose(){return page.locator('.typing-hands [data-hand]').evaluateAll(es=>es.map(e=>{const m=e.transform.baseVal.consolidate().matrix;return [m.a,m.b,m.c,m.d,m.e,m.f];}));}
  const home=await pose();assert.ok(home[0][1]>0&&home[1][1]<0,'Both hands form a shallow inverted V at rest');
  const wristX=home.map((m,side)=>m[0]*(side===0?205:470)+m[2]*330+m[4]);
  assert.ok(wristX[0]<188&&wristX[1]>488,'Wrists sit outside the centers of their four home fingertips');
  async function press(code,key=code.replace('Key','')){
   // Composing Enter demonstrates the movement without submitting an answer.
   await page.locator('#kbdInput').dispatchEvent('keydown',{code,key,isComposing:code==='Enter'});await page.waitForTimeout(650);
  }
  async function release(code){await page.locator('#kbdInput').dispatchEvent('keyup',{code});await page.waitForTimeout(650);}
  async function atHome(){const p=await pose();p.forEach((m,side)=>m.forEach((n,i)=>assert.ok(Math.abs(n-home[side][i])<.05,'Hand returns to its angled home pose')));}
  async function contact(finger,code){
   const measurement=await page.evaluate(({finger,code})=>{
    const f=document.querySelector(`[data-finger="${finger}"]`),key=document.querySelector(`[data-code="${code}"] rect`);
    const local=f.getPointAtLength(f.getTotalLength()),p=new DOMPoint(local.x,local.y).matrixTransform(f.parentElement.transform.baseVal.consolidate().matrix);
    return {distance:Math.hypot(p.x-(+key.getAttribute('x')+(+key.getAttribute('width'))/2),p.y-(+key.getAttribute('y')+22)),length:f.getTotalLength()};
   },{finger,code});
   assert.ok(measurement.distance<1,'Fingertip reaches its key');return measurement;
  }
  await atHome();
  // Eight fingers have two interphalangeal creases; each thumb has one.
  assert.equal(await page.locator('.typing-joint').count(),18);
  for(const [i,code]of [[0,'KeyA'],[1,'KeyS'],[2,'KeyD'],[3,'KeyF'],[6,'KeyJ'],[7,'KeyK'],[8,'KeyL'],[9,'Semicolon']])await contact(i,code);
  assert.ok(await page.locator('[data-hand=left] .palm').evaluate(e=>e.getBBox().y<210),'Hand back sits close to the keys');
  await page.screenshot({path:path.join(out,`${width}-home.png`),fullPage:true});
  await press('KeyF');await atHome();await contact(3,'KeyF');await release('KeyF');
  await press('KeyR');const near=await pose();assert.ok(Math.abs(near[0][4]-home[0][4])+Math.abs(near[0][5]-home[0][5])>2);assert.equal(near[1][4],home[1][4]);await contact(3,'KeyR');await release('KeyR');await atHome();
  await press('Enter','Enter');const enter=await pose();assert.ok(enter[1][4]-home[1][4]>65,'Enter carries the right hand to the side');assert.ok(Math.abs(enter[0][4]-home[0][4])<.05);
  await contact(9,'Enter');await page.screenshot({path:path.join(out,`${width}-enter.png`),fullPage:true});await release('Enter');await atHome();
  await press('Backspace','Backspace');const back=await pose();assert.ok(back[1][5]<enter[1][5]-20,'Backspace carries the hand farther up');
  const tip=await contact(9,'Backspace');assert.ok(tip.length<110,'A far key does not stretch the pinky into a long straight finger');
  await page.screenshot({path:path.join(out,`${width}-backspace.png`),fullPage:true});
  await page.locator('#kbdInput').dispatchEvent('keydown',{code:'Backspace',key:'Backspace',repeat:true});await page.waitForTimeout(300);
  assert.ok(Math.abs((await pose())[1][4]-back[1][4])<.05,'Repeating a key never accumulates hand displacement');await release('Backspace');await atHome();
  await press('ShiftLeft','Shift');await press('KeyP','P');await contact(0,'ShiftLeft');await contact(9,'KeyP');
  await release('KeyP');await release('ShiftLeft');await atHome();
  await press('Backspace','Backspace');await page.evaluate(()=>resetGame());await page.waitForTimeout(650);await atHome();assert.equal(await page.locator('.typing-key.pressed').count(),0);
  await press('Enter','Enter');await page.locator('#kbdInput').dispatchEvent('blur');await page.waitForTimeout(650);await atHome();
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('#kbdInput').dispatchEvent('keydown',{code:'Enter',key:'Enter',isComposing:true});await contact(9,'Enter');
  await page.locator('#kbdInput').dispatchEvent('keyup',{code:'Enter'});await atHome();
  await page.evaluate(()=>{ST.tail='す';setCurrentInput('');});
  assert.match(await page.locator('#typingCue').innerText(),/Backspace/);
  assert.equal(await page.locator('.hint-next').count(),0,'Empty input never asks to submit');
  await page.locator('#kbdInput').fill('すいか');assert.equal(await page.locator('[data-code=Enter].hint-next').count(),1);assert.match(await page.locator('#typingCue').innerText(),/Enter.*すいか.*つなげ/);
  assert.ok(await page.locator('#typingCueKey').isVisible());assert.match(await page.locator('#typingCueKey').innerText(),/Enter.*\nここを おす/);
  assert.equal(await page.locator('#typingKeySpotlight').getAttribute('data-key'),'Enter');
  assert.equal(await page.locator('#typingKeySpotlight rect').evaluate(e=>getComputedStyle(e).fill),'rgb(26, 255, 160)','Enter shines across its whole face');
  assert.ok(await page.locator('#typingKeySpotlight').evaluate(e=>e.parentNode.lastElementChild===e),'The bright key is drawn above the hands');
  assert.ok(await page.locator('#typingKeySpotlight rect').evaluate(e=>{const r=e.getBoundingClientRect(),g=document.getElementById('keyboardGuide').getBoundingClientRect(),c=document.getElementById('colCenter').getBoundingClientRect();return r.top>=Math.max(0,g.top,c.top)&&r.bottom<=Math.min(innerHeight,g.bottom,c.bottom); }),'The glowing Enter key and instruction are visible together without scrolling');
  await page.screenshot({path:path.join(out,`${width}-enter-cue.png`),fullPage:true});
  await page.locator('#kbdInput').dispatchEvent('compositionstart');assert.equal(await page.locator('.hint-next').count(),0);assert.equal(await page.locator('#typingCue').getAttribute('data-action'),'compose');
  assert.equal(await page.locator('#typingKeySpotlight').isVisible(),false,'No connect spotlight during IME conversion');
  await page.locator('#kbdInput').dispatchEvent('keydown',{key:'Enter',code:'Enter',isComposing:true});assert.equal(await page.evaluate(()=>ST.history.length),0);await page.locator('#kbdInput').dispatchEvent('keyup',{code:'Enter'});
  await page.locator('#kbdInput').dispatchEvent('compositionend');assert.equal(await page.locator('.hint-next').count(),1);
  await page.locator('#kbdInput').fill('りんご');assert.equal(await page.locator('[data-code=Backspace].hint-edit').count(),1);assert.equal(await page.locator('.hint-next').count(),0);
  assert.match(await page.locator('#typingCueKey').innerText(),/Backspace/);assert.equal(await page.locator('#typingKeySpotlight').getAttribute('data-key'),'Backspace');
  assert.equal(await page.locator('#typingKeySpotlight rect').evaluate(e=>getComputedStyle(e).fill),'rgb(255, 225, 102)','Backspace shines across its whole face');
  await page.screenshot({path:path.join(out,`${width}-backspace-cue.png`),fullPage:true});
  await page.locator('#kbdInput').fill('すぷーん');assert.equal(await page.locator('#typingCue').getAttribute('data-action'),'edit');
  await page.evaluate(()=>{ST.used.add('すいか');setCurrentInput('すいか');});assert.equal(await page.locator('.hint-next').count(),0);
  await page.evaluate(()=>{ST.used.clear();setCurrentInput('すいか');ST.cpuBusy=true;ShiritoriKeyboardGuide.refresh();});assert.equal(await page.locator('.hint-next').count(),0,'Busy turns never suggest Enter');
  await page.evaluate(()=>{ST.cpuBusy=false;ST.tail='';resetGame();});
  await page.evaluate(()=>{ST.skipLinkAnimation=true;});
  await page.locator('#kbdInput').fill('りす');assert.equal(await page.locator('.hint-next').count(),1);
  await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.history.length===2&&!ST.cpuBusy);
  assert.equal(await page.evaluate(()=>ST.history.filter(e=>e.speaker==='あなた').length),1,'Suggested Enter submits exactly once');
  assert.match(await page.locator('#typingCue').innerText(),/Backspace/);assert.equal(await page.locator('.hint-next').count(),0,'Next word starts with editing guidance, not stale Enter guidance');
  assert.deepEqual(errors,[]);await page.close();
 }
 console.log(JSON.stringify({passed:true,viewports:4,out}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
