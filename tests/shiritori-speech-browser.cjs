const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.SHIRITORI_ROOT||path.resolve(__dirname,'..');
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
      assert.equal(await page.evaluate(()=>ST.speechConfirm),true);
      assert.equal(await page.locator('#speechConfirm').isChecked(),true);
      assert.equal(await page.evaluate(()=>ST.speechPrompt),true);
      assert.equal(await page.locator('#speechPrompt').isChecked(),true);
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
      await word('ちがうよ');
      // Spaces, mixed kanji/kana, and partial ambiguous readings in a long word.
      for(const text of ['コクサイ　レンゴウ','国際 れんごう','日本 こく 憲法']){
        await word(text);
        assert.equal(await page.evaluate(()=>ST.currentInput),text.includes('日本')?'にほんこくけんぽう':'こくさいれんごう');
        assert.equal(await page.evaluate(()=>ST.history.length),0);
        await word('ちがうよ');
      }
      await word('車');
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
      // Unknown kanji still retries. Ambiguous readings now connect by the tail.
      await word('未登録超難解語');assert.equal(await page.evaluate(()=>ST.currentInput),'');
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('ひとつに できませんでした'))));
      await page.evaluate(()=>{resetGame(false);ST.tail='か';});await listening();
      const automaticStart=await page.evaluate(()=>voiceLog.length);
      await word('金');
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});await listening();
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'かね');
      assert.equal(await page.evaluate(start=>voiceLog.slice(start).some(t=>t.includes('ばんごう')||t.includes('と認識')),automaticStart),false);
      // No matching candidate: retry without committing or asking for a number.
      await page.evaluate(()=>{resetGame(false);ST.tail='ぬ';});await listening();
      await word('金');
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('「ぬ」から はじまる'))));
      await page.evaluate(()=>{resetGame(false);ST.tail='か';ST.used.add('かね');});await listening();
      await word('金');assert.equal(await page.evaluate(()=>ST.history.length),0);
      // Short-word fallback: the primary recognition is wrong, but an alternative connects.
      await page.evaluate(()=>{resetGame(false);ST.tail='え';});await listening();
      assert.equal(await page.evaluate(()=>window.mic.maxAlternatives),5);
      await page.evaluate(()=>{
        const mic=window.mic;window.mic=null;
        const result=[{transcript:'キ'},{transcript:'絵'}];result.isFinal=true;
        mic.onresult({resultIndex:0,results:[result]});mic.onend();
      });await listening();
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});await listening();
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'え');
      await page.evaluate(()=>resetGame(false));await listening();
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
      // Confirmation OFF submits directly, including after selecting an ambiguous reading.
      await page.evaluate(()=>{showPage('settings');setSettingsTab('input');});
      await page.locator('#speechConfirm').uncheck();
      assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-settings')).speechConfirm),false);
      await page.evaluate(()=>resetGame(false));await enter();
      assert.match(await page.locator('#speechInstructions').innerText(),/そのまま/);
      const offStart=await page.evaluate(()=>voiceLog.length);
      await word('車');
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'くるま');
      assert.equal(await page.evaluate(start=>voiceLog.slice(start).some(t=>t.includes('と認識')||t.includes('オーケー')),offStart),false);
      // Disable the independent turn prompt: initial and next turns still listen automatically.
      await page.evaluate(()=>{showPage('settings');setSettingsTab('input');});
      await page.locator('#speechPrompt').uncheck();
      assert.equal(await page.evaluate(()=>ST.speechConfirm),false);
      assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-settings')).speechPrompt),false);
      await page.evaluate(()=>resetGame(false));
      const quietStart=await page.evaluate(()=>voiceLog.length);await enter();
      await word('りんご');
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'りんご');
      assert.equal(await page.evaluate(start=>voiceLog.slice(start).some(t=>t.includes('しゃべってください')||t.includes('と認識')),quietStart),false);
      await page.evaluate(()=>{resetGame(false);ST.tail='い';});await listening();
      await word('りんご');assert.equal(await page.evaluate(()=>ST.history.length),0);
      await page.evaluate(()=>resetGame(false));await listening();
      await word('金');
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:25000});
      assert.equal(await page.evaluate(()=>ST.history[0].reading),'かね');
      assert.equal(await page.evaluate(()=>echoStarts),0);
      // Reload always returns to a literacy input; settings is the sole mic entrance.
      await page.reload();await page.waitForFunction(()=>ST.wlLoaded);
      assert.equal(await page.evaluate(()=>ST.inputMode),'canvas');assert.equal(await page.evaluate(()=>mics.length),0);
      assert.equal(await page.evaluate(()=>ST.speechConfirm),false);
      assert.equal(await page.evaluate(()=>ST.speechPrompt),false);
      await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();document.getElementById('shiriNotice').close();showPage('settings');setSettingsTab('input');ST.skipLinkAnimation=true;});
      assert.equal(await page.locator('#speechConfirm').isChecked(),false);
      assert.equal(await page.locator('#speechPrompt').isChecked(),false);
      await page.locator('#speechConfirm').check();await enter();
      assert.equal(await page.evaluate(()=>ST.speechPrompt),false);
      assert.equal(await page.evaluate(()=>voiceLog.some(t=>t.includes('しゃべってください'))),false);
      await word('りんご');assert.equal(await page.evaluate(()=>ST.history.length),0);
      assert.ok(await page.evaluate(()=>voiceLog.some(t=>t.includes('りんご と認識'))));
      // Changing the setting cancels a pending confirmation without committing it.
      await page.evaluate(()=>{showPage('settings');setSettingsTab('input');});
      await page.locator('#speechConfirm').uncheck();
      assert.equal(await page.evaluate(()=>ST.currentInput),'');
      await page.evaluate(()=>showPage('game'));await listening();
      assert.equal(await page.evaluate(()=>ST.history.length),0);
      await page.evaluate(()=>{showPage('settings');setSettingsTab('input');ST.tail='い';});
      await page.locator('#speechPrompt').check();
      assert.equal(await page.evaluate(()=>ST.speechConfirm),false);
      const enabledStart=await page.evaluate(()=>voiceLog.length);
      await page.evaluate(()=>showPage('game'));await listening();
      assert.ok(await page.evaluate(start=>voiceLog.slice(start).some(t=>t.includes('「い」から はじまる')),enabledStart));
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
