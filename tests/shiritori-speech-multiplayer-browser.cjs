const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'application/octet-stream');fs.createReadStream(file).pipe(res);
});
function mocks(){
 window.voiceLog=[];window.mics=[];window.mic=null;window.echoStarts=0;
 let current=null;
 const synth={speaking:false,cancel(){if(current)clearTimeout(current.timer);current=null;this.speaking=false;},getVoices(){return [];},speak(u){
  voiceLog.push(u.text);this.speaking=true;current=u;u.onstart?.();
  if(window.holdNextTurn&&u.text.startsWith('つぎは ')){window.heldTurn=u;window.holdNextTurn=false;return;}
  u.timer=setTimeout(()=>{if(current!==u)return;this.speaking=false;current=null;u.onend?.();},20);
 }};
 Object.defineProperty(window,'speechSynthesis',{value:synth,configurable:true});
 window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
 window.SpeechRecognition=class{
  start(){if(synth.speaking||window.mic)echoStarts++;window.mic=this;mics.push(this);this.onstart?.();}
  abort(){if(window.mic===this)window.mic=null;}
  finish(text){if(window.mic===this)window.mic=null;const result=[{transcript:text}];result.isFinal=true;this.onresult?.({resultIndex:0,results:[result]});this.onend?.();}
 };
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({channel:'chrome',headless:true});
 try{
  for(const width of [1280,390,320]){
   const page=await browser.newPage({viewport:{width,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
   await page.addInitScript(mocks);
   await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   async function dismiss(){await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();document.getElementById('shiriNotice').close();ST.skipLinkAnimation=true;getCpuDelay=()=>0;});}
   async function setup(count,cpu,mode='coop'){
    await page.locator('#btnPlayers').click();await page.locator('#playerCount').selectOption(String(count));
    await page.locator('#includeCpu').setChecked(cpu);await page.locator('#playRule').selectOption(mode);
    await page.locator('#playerSetupForm button[type=submit]').click();
   }
   async function listening(){await page.waitForFunction(()=>!!window.mic,{},{timeout:15000});}
   async function enter(){await page.evaluate(()=>{showPage('settings');setSettingsTab('input');ST.speechConfirm=false;ST.speechPrompt=false;});await page.locator('#speechEnter').click();await listening();}
   async function spoken(text,length,id){
    await listening();await page.evaluate(t=>window.mic.finish(t),text);
    await page.waitForFunction(({length,id})=>ST.history.length===length&&ShiritoriPlayers.current().id===id&&!ST.cpuBusy&&!!window.mic,{length,id},{timeout:25000});
    assert.equal(await page.locator('#handoff').isVisible(),false);
   }
   await dismiss();await setup(2,false);await enter();
   assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-players-v1')).inputs[0]),'speech');
   await spoken('りす',1,'human1');
   assert.equal(await page.evaluate(()=>ST.inputMode),'speech','Unconfigured next player inherits voice');
   assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-players-v1')).inputs[1]),'speech');
   await spoken('すいか',2,'human0');
   assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),['human0','human1']);
   assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.startsWith('つぎは プレイヤー2'))));
   await page.reload();await page.waitForFunction(()=>ST.wlLoaded);
   assert.equal(await page.evaluate(()=>ST.inputMode),'speech','Voice mode restored from each player profile');
   assert.equal(await page.evaluate(()=>mics.length),0,'Title/notice blocks the mic on reload');
   await dismiss();await listening();
   // An explicit keyboard preference survives voice handoff in both directions.
   await page.evaluate(()=>{switchIn('kbd');setCurrentInput('りす');return submitWord();});await listening();
   assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human1');
   assert.equal(await page.locator('#handoff').isVisible(),false);
   await page.evaluate(()=>window.mic.finish('すいか'));await page.locator('#handoff').waitFor();
   assert.equal(await page.evaluate(()=>window.mic),null);
   await page.locator('#takeTurn').click();assert.equal(await page.evaluate(()=>ST.inputMode),'kbd');
   await setup(2,true);await enter();
   await page.evaluate(()=>{cpuChoose=async()=>rowForLevel(await dictionary.reading('かめ'));});
   await spoken('りす',1,'human1');await spoken('すいか',3,'human0');
   assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),['human0','human1','cpu']);
   // Pausing voice stays paused when another player takes over.
   await page.locator('#speechPause').click();await page.locator('#giveUp').click();
   await page.waitForFunction(()=>ShiritoriPlayers.current().id==='human1'&&!ST.cpuBusy);
   assert.equal(await page.evaluate(()=>window.mic),null);
   assert.equal(await page.locator('#speechResume').isVisible(),true);
   await page.locator('#speechResume').click();await listening();
   // Reset during a held announcement cannot advance the new game.
   await page.evaluate(()=>{window.holdNextTurn=true;window.mic.finish('めだか');});
   await page.waitForFunction(()=>!!window.heldTurn);
   assert.equal(await page.evaluate(()=>ST.cpuBusy),true);
   await page.evaluate(()=>{resetGame(false);window.heldTurn.onend?.();});await listening();
   assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');
   assert.equal(await page.evaluate(()=>ST.history.length),0);
   await setup(6,true);await enter();await page.evaluate(()=>{cpuChoose=async()=>null;});
   for(const [i,text] of ['りす','すいか','かめ','めだか','かさ','さる'].entries())await spoken(text,i+1,`human${(i+1)%6}`);
   assert.deepEqual(await page.evaluate(()=>ST.history.map(e=>e.playerId)),Array.from({length:6},(_,i)=>`human${i}`));
   // Versus mode: eliminate only the speaker, skip them, and replay by voice.
   await setup(3,false,'versus');await enter();await spoken('りす',1,'human1');
   await page.evaluate(()=>window.mic.finish('すいみん'));
   await page.waitForFunction(()=>ShiritoriPlayers.current().id==='human2'&&!ST.cpuBusy&&!!window.mic);
   assert.equal(await page.locator('.player-chip.eliminated').count(),1);
   assert.equal(await page.evaluate(()=>ST.history.length),1);
   await spoken('すいか',2,'human0');
   await page.evaluate(()=>window.mic.finish('かばん'));
   await page.waitForFunction(()=>ST.gameOver&&!!window.mic);
   assert.equal(await page.evaluate(()=>ST.history.length),2);
   await page.evaluate(()=>window.mic.finish('もういっかい'));await listening();
   assert.equal(await page.evaluate(()=>ST.gameOver),false);
   assert.equal(await page.evaluate(()=>ShiritoriPlayers.current().id),'human0');
   assert.equal(await page.locator('.player-chip.eliminated').count(),0);
   assert.equal(await page.evaluate(()=>echoStarts),0,'Microphone never starts over speech or another mic');
   assert.deepEqual(errors,[]);await page.close();console.log(`multiplayer speech ${width}px passed`);
  }
  const page=await browser.newPage();await page.addInitScript(()=>{
   window.SpeechRecognition=undefined;window.webkitSpeechRecognition=undefined;
   localStorage.setItem('shiri-players-v1',JSON.stringify({count:2,cpu:false,mode:'coop',names:[],inputs:['speech','speech']}));
  });
  await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,body:'{}'}));
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  assert.equal(await page.evaluate(()=>ST.inputMode),'canvas');assert.equal(await page.locator('#speechEnter').isDisabled(),true);
  await page.close();console.log('unsupported browser restores handwriting passed');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
