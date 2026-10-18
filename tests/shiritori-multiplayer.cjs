const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/multiplayer');
const server=http.createServer((req,res)=>{
 const file=path.join(root,decodeURIComponent(req.url.split('?')[0]));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8'}[path.extname(file)]||'application/octet-stream'));fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
 const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({channel:'chrome',headless:true});
 try{
 for(const [width,height]of [[1280,900],[390,844],[320,740],[844,390]]){
  const page=await browser.newPage({viewport:{width,height}}),errors=[];page.on('pageerror',e=>{errors.push(e.message);console.error('PAGE',e.stack);});
  await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await require('./shiritori-r2-fixture.cjs')(page);
  await page.goto(origin+'/shiritori.html');
  await page.waitForFunction(()=>ST.wlLoaded,{},{timeout:15000});
  await page.locator('#noticeStart').click();
  await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();ST.voice=false;ST.skipLinkAnimation=true;getCpuDelay=()=>0;});
  async function setup(count,cpu,mode){
   await page.locator('#btnPlayers').click();await page.locator('#playerCount').selectOption(String(count));await page.locator('#includeCpu').setChecked(cpu);await page.locator('#playRule').selectOption(mode);
   await page.locator('#playerNames input').nth(0).fill('あお');
   await page.locator('#playerSetupForm button[type=submit]').click();await page.evaluate(()=>switchIn('kbd'));
  }
  async function word(text){await page.locator('#kbdInput').fill(text);await page.locator('#btnOk').click();}
  async function ready(){await page.locator('#handoff').waitFor();await page.locator('#takeTurn').click();}
  await setup(2,false,'versus');
  assert.equal(await page.locator('#playerStrip .player-chip').count(),2);
  for(const id of ['btnCharMode','btnReset'])assert.ok(await page.locator('#'+id).isVisible());
  await page.locator('#btnCharMode').click();assert.equal(await page.evaluate(()=>ST.charMode),'katakana');await page.locator('#btnCharMode').click();
  await page.locator('#kbdInput').focus();await page.keyboard.down('r');
  assert.ok(await page.locator('[data-code=KeyR]').evaluate(e=>e.classList.contains('pressed')));
  assert.match(await page.locator('#typingAction').innerText(),/左ひとさし/);
  await page.screenshot({path:path.join(out,`${width}-keyboard.png`),fullPage:true});
  await page.keyboard.up('r');assert.equal(await page.locator('.typing-key.pressed').count(),0);
  await page.locator('#typingDisplay').selectOption('keys');assert.equal(await page.locator('.typing-hands').isVisible(),false);
  await page.locator('#typingDisplay').selectOption('off');assert.equal(await page.locator('#typingSvg').isVisible(),false);
  await page.locator('#typingDisplay').selectOption('hands');
  // IME Enter cannot commit; normal physical input still works.
  await page.locator('#kbdInput').fill('りす');await page.locator('#kbdInput').dispatchEvent('keydown',{key:'Enter',isComposing:true});assert.equal(await page.evaluate(()=>ST.history.length),0);
  await word('りす');await page.locator('#handoff').waitFor();
  assert.equal(await page.evaluate(()=>ST.cpuBusy),true);
  await page.evaluate(async()=>{setCurrentInput('すいか');await submitWord();});assert.equal(await page.evaluate(()=>ST.history.length),1,'No input during handoff');
  await page.screenshot({path:path.join(out,`${width}-handoff.png`),fullPage:true});
  await ready();assert.equal(await page.evaluate(()=>ST.currentInput),'');
  await page.evaluate(()=>switchIn('btn'));await page.evaluate(()=>{setCurrentInput('すいか');return submitWord();});await ready();
  assert.equal(await page.evaluate(()=>ST.inputMode),'kbd','Each player restores their own input');
  assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),['human0','human1']);
  await word('かばん');await page.waitForFunction(()=>ST.gameOver);
  assert.match(await page.locator('#scMain').innerText(),/プレイヤー2.*かち/);
  assert.equal(await page.evaluate(()=>ST.tail),'か','Ending N does not overwrite valid tail');
  await page.locator('#replayBtn').click();assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.cpuBusy),false);
  await setup(2,true,'versus');
  await page.evaluate(()=>{window.savedCpuChoose=cpuChoose;cpuChoose=()=>lookupRow('かめ');});
  await word('りす');await ready();await page.evaluate(()=>switchIn('kbd'));await word('すいか');await ready();
  assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),['human0','human1','cpu']);
  assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');
  // CPU elimination skips it thereafter; simultaneous reset invalidates CPU work.
  await page.evaluate(()=>{cpuChoose=()=>null;});
  await word('めだか');await ready();await page.evaluate(()=>switchIn('kbd'));await word('かさ');await ready();
  assert.equal(await page.locator('.player-chip.eliminated').count(),1);
  await page.evaluate(()=>{cpuChoose=window.savedCpuChoose;resetGame();});
  if(width===1280){
   // A reset while the CPU waits cannot add an old move to the new game.
   await page.evaluate(()=>{getCpuDelay=()=>250;});
   await word('りす');await ready();await page.evaluate(()=>switchIn('kbd'));await word('すいか');
   await page.waitForFunction(()=>ShiritoriPlayers.current().cpu&&ST.cpuBusy);
   await page.locator('#btnReset').click();await page.waitForTimeout(350);
   assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.cpuBusy),false);
   await page.evaluate(()=>{getCpuDelay=()=>0;});
  }
  await setup(2,false,'coop');await word('みかん');assert.equal(await page.evaluate(()=>ST.gameOver),false);assert.equal(await page.evaluate(()=>ST.history.length),0);
  await word('りす');await ready();await page.evaluate(()=>switchIn('kbd'));await word('りんご');assert.equal(await page.evaluate(()=>ST.history.length),1,'Wrong head stays on same turn');
  await page.locator('#giveUp').click();await ready();assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');
  await setup(6,true,'versus');assert.equal(await page.locator('.player-chip').count(),7);
  await page.screenshot({path:path.join(out,`${width}-seven-players.png`),fullPage:true});
  if(width===1280||width===390){
   await page.evaluate(()=>{cpuChoose=()=>null;});
   for(const text of ['りす','すいか','かめ','めだか','かさ','さる']){
    await page.evaluate(()=>switchIn('kbd'));await word(text);await ready();
    assert.ok(await page.locator('.player-chip[aria-current]').evaluate(e=>{const a=e.getBoundingClientRect(),b=e.parentElement.getBoundingClientRect();return a.left>=b.left-2&&a.right<=b.right+2;}),'Current player remains visible in horizontal roster');
   }
   assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),Array.from({length:6},(_,i)=>`human${i}`));
   assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');await page.locator('#btnReset').click();
   await page.evaluate(()=>{cpuChoose=window.savedCpuChoose;});
  }
  await page.locator('#giveUp').click();await ready();assert.equal(await page.locator('.player-chip.eliminated').count(),1);
  await page.locator('#giveUp').click();await page.locator('#restartPlayers').click();assert.equal(await page.locator('.player-chip.eliminated').count(),0);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'No horizontal page overflow');
  await page.reload();await page.waitForFunction(()=>ST.wlLoaded);assert.equal(await page.locator('.player-chip').count(),7,'Roster persists');
  if(width===1280){
   await page.locator('#noticeStart').click();await page.emulateMedia({reducedMotion:'reduce'});
   await page.evaluate(()=>launchGame(true));assert.ok(await page.locator('#playerSetup').isVisible(),'Startup offers roster selection');await page.locator('#cancelPlayers').click();
   await setup(1,false,'versus');assert.equal(await page.locator('#playerRuleLabel').innerText(),'みんなで 0語','Solo without CPU uses cooperative rules');
   await word('りす');await ready();assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');
  }
  assert.deepEqual(errors,[]);await page.close();
 }
 console.log(JSON.stringify({passed:true,viewports:4,out}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
