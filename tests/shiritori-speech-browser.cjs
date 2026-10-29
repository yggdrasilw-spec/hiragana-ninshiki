const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.SHIRITORI_ROOT||path.resolve(__dirname,'..');
const ambiguous=Object.entries(JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-speech-readings.json'),'utf8'))).find(([k,v])=>v.length>1&&v.length<=5&&v.join('').length<=40&&/[一-龥]/.test(k));
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(file).pipe(res);
});
function mocks(){
  window.voiceLog=[];window.mics=[];window.mic=null;window.echoStarts=0;
  let current=null;
  const synth={speaking:false,cancel(){if(current)clearTimeout(current.timer);current=null;this.speaking=false;},getVoices(){return [];},speak(u){
    window.voiceLog.push(u.text);this.speaking=true;current=u;u.onstart?.();
    u.timer=setTimeout(()=>{if(current!==u)return;this.speaking=false;current=null;u.onend?.();},20);
  }};
  Object.defineProperty(window,'speechSynthesis',{value:synth,configurable:true});
  Object.defineProperty(document,'hidden',{get:()=>window.testHidden===true,configurable:true});
  window.SpeechSynthesisUtterance=class{constructor(text){this.text=text;}};
  window.SpeechRecognition=class{
    start(){if(synth.speaking||window.mic)window.echoStarts++;window.mic=this;window.mics.push(this);this.onstart?.();}
    abort(){if(window.mic===this)window.mic=null;}
    finish(text,error){if(window.mic===this)window.mic=null;
      if(error)this.onerror?.({error});
      if(text){const r=[{transcript:text}];r.isFinal=true;this.onresult?.({resultIndex:0,results:[r]});}
      this.onend?.();
    }
  };
}
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
  const browser=await chromium.launch({headless:true,channel:'chrome'});
  try{
    for(const width of [1280,390,320]){
      const page=await browser.newPage({viewport:{width,height:900}}),errors=[],requests=[];let blockReadings=false;
      page.on('pageerror',e=>errors.push(e.message));
      await page.addInitScript(mocks);
      await page.route('**/*',route=>{const url=route.request().url();requests.push(url);if(blockReadings&&url.includes('speech-readings.json'))return route.abort();return url.startsWith(origin)?route.continue():route.fulfill({status:200,contentType:'application/json',body:'{}'});});
      await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
      await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();ST.skipLinkAnimation=true;ST.voice=false;});
      await page.locator('#noticeStart').click();
      assert.equal(await page.locator('#inTabs button').count(),3);
      assert.equal(await page.locator('#modeSpeech').isVisible(),false);
      assert.equal(requests.filter(u=>u.includes('speech-readings')).length,0);
      async function enter(){await page.evaluate(()=>{showPage('settings');setSettingsTab('input');});await page.locator('#speechEnter').click();await listening();}
      async function listening(){await page.waitForFunction(()=>!!window.mic,{},{timeout:12000});}
      async function word(text){await listening();await page.evaluate(t=>window.mic.finish(t),text);await listening();}
      await enter();assert.equal(await page.evaluate(()=>ST.inputMode),'speech');
      assert.equal(await page.locator('#speechResume').isVisible(),false);
      await page.evaluate(()=>{const r=[{transcript:'りんご'}];r.isFinal=false;window.mic.onresult({resultIndex:0,results:[r]});window.mic.finish('');});
      await listening();assert.equal(await page.evaluate(()=>ST.currentInput),'');
      await page.evaluate(()=>{ST.charMode='katakana';});
      await word('リンゴ');assert.equal(await page.evaluate(()=>ST.currentInput),'りんご');
      assert.equal(await page.locator('#speechReading').innerText(),'リンゴ');
      await page.evaluate(()=>{window.oldMic=window.mics[window.mics.length-2];window.oldMic.onend?.();});
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('りんご と認識'))));
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      await word('ちがうよ');assert.equal(await page.evaluate(()=>ST.currentInput),'');
      await page.evaluate(()=>{ST.charMode='hiragana';});
      assert.ok(await page.evaluate(()=>voiceLog.includes('もういちど、しゃべってください。')));
      blockReadings=true;await word('車');assert.equal(await page.evaluate(()=>ST.currentInput),'');blockReadings=false;
      await word('車');assert.equal(await page.evaluate(()=>ST.currentInput),'くるま');
      await page.screenshot({path:path.join(process.env.SPEECH_SCREENSHOTS||root,`speech-${width}.png`)});
      await word('オーケー');
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});await listening();
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'くるま');
      assert.equal(await page.evaluate(()=>echoStarts),0);
      assert.equal(await page.locator('#modeSpeech').isVisible(),true);
      // A wrong first letter and a repeated word produce audible feedback and retry.
      await page.evaluate(()=>{resetGame(false);ST.tail='い';});await listening();
      await word('りんご');await word('オーケー');
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('ではじまることば'))));
      // Late results from an aborted recognition must not refill or commit input.
      await page.evaluate(()=>{window.stale=window.mic;window.staleResult=window.mic.onresult;window.staleEnd=window.mic.onend;showPage('settings');const r=[{transcript:'りんご'}];r.isFinal=true;staleResult({resultIndex:0,results:[r]});staleEnd();});
      assert.equal(await page.evaluate(()=>window.mic),null);
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      await page.evaluate(()=>resetGame(false));await enter();
      // Ambiguous / unknown kanji may never become a guessed reading.
      await word('未登録超難解語');assert.equal(await page.evaluate(()=>ST.currentInput),'');
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('ひとつに できませんでした'))));
      assert.ok(ambiguous);await word(ambiguous[0]);assert.equal(await page.evaluate(()=>ST.currentInput),'');
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('ばんごうを いってね'))));
      await word('6番');assert.equal(await page.evaluate(()=>ST.currentInput),'');
      await word('1番');assert.equal(await page.evaluate(()=>ST.currentInput),ambiguous[1][0]);
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      await word('ちがうよ');assert.equal(await page.evaluate(()=>ST.currentInput),'');
      // Unknown confirmations cannot commit, and stop works without a tap.
      await word('りんご');await word('えっと');assert.equal(await page.evaluate(()=>ST.history.length),0);
      await page.evaluate(()=>window.mic.finish('ストップ'));
      await page.locator('#speechResume').waitFor({state:'visible'});
      assert.equal(await page.evaluate(()=>window.mic),null);
      await page.locator('#speechResume').click();await listening();
      await page.evaluate(()=>{window.testHidden=true;document.dispatchEvent(new Event('visibilitychange'));});
      assert.equal(await page.evaluate(()=>window.mic),null);
      await page.evaluate(()=>{window.testHidden=false;document.dispatchEvent(new Event('visibilitychange'));});
      assert.equal(await page.evaluate(()=>window.mic),null);
      await page.locator('#speechResume').click();await listening();
      await page.evaluate(()=>{ST.voice=false;});
      await page.waitForFunction(()=>!window.mic);assert.equal(await page.locator('#speechResume').isVisible(),true);
      await page.locator('#speechResume').click();await listening();
      assert.equal(await page.evaluate(()=>ST.voice),true);
      await page.evaluate(()=>window.mic.finish('', 'not-allowed'));
      assert.match(await page.locator('#speechStatus').innerText(),/マイク許可/);
      assert.equal(await page.evaluate(()=>window.mic),null);
      await page.locator('#speechResume').click();await listening();
      for(let i=0;i<3;i++){await page.evaluate(()=>window.mic.finish(''));if(i<2)await listening();}
      assert.match(await page.locator('#speechStatus').innerText(),/おやすみ中/);
      await page.locator('#speechResume').click();await listening();
      // End-game and restart work with voice, and never overlap CPU speech.
      await page.evaluate(()=>resetGame(false));await listening();
      await word('みかん');await page.evaluate(()=>window.mic.finish('オーケー'));
      await page.waitForFunction(()=>ST.gameOver);await listening();
      await page.evaluate(()=>window.mic.finish('もういっかい'));await listening();
      assert.equal(await page.evaluate(()=>ST.gameOver),false);assert.equal(await page.evaluate(()=>ST.history.length),0);
      assert.equal(await page.evaluate(()=>echoStarts),0);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      // Reload always returns to a literacy input; settings is the sole mic entrance.
      await page.reload();await page.waitForFunction(()=>ST.wlLoaded);
      assert.equal(await page.evaluate(()=>ST.inputMode),'canvas');assert.equal(await page.evaluate(()=>mics.length),0);
      assert.deepEqual(errors,[]);
      await page.close();console.log(`speech ${width}px passed`);
    }
    const page=await browser.newPage();await page.addInitScript(()=>{window.SpeechRecognition=undefined;window.webkitSpeechRecognition=undefined;});
    await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,body:'{}'}));
    await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
    assert.equal(await page.locator('#speechEnter').isDisabled(),true);await page.close();
    console.log('unsupported browser passed');
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
