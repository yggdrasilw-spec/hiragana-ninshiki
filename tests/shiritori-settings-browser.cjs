const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/settings');
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);res.end();return;}
 res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'}[path.extname(file)]||'application/octet-stream'));
 fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
 const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true,...(process.env.QA_EXECUTABLE?{executablePath:process.env.QA_EXECUTABLE}:{channel:'msedge'})});
 try{
 for(const [name,width,height] of [['desktop',1280,900],['mobile',390,844],['small',320,640]]){
  const page=await browser.newPage({viewport:{width,height}}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  await page.locator('#noticeStart').click();
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.evaluate(async()=>{ST.voice=false;await launchGame();showPage('settings');});
  assert.equal(await page.locator('.lv-btn').count(),5);
  assert.equal(await page.locator('[data-genre]').count(),16);
  assert.equal(await page.locator('[data-settings-group="input"]').first().isVisible(),false);
  const counts=await page.evaluate(()=>[1,2,3,4,5].map(level=>{ST.level=level;return dictionary.count(ST.level,ST.cpuGenres);}));
  assert.ok(counts.every((v,i)=>!i||v>counts[i-1]));
  assert.equal(counts[4],await page.evaluate(()=>ST.whitelist.length));
  assert.equal(await page.evaluate(()=>{ST.level=1;return getPool().some(r=>['あいち','あきおおたちょう','あきたかたし'].includes(r.reading));}),false);
  assert.deepEqual(await page.evaluate(async()=>rowForLevel(await dictionary.reading('いし')).words),['石']);
  assert.ok(await page.evaluate(async()=>{ST.level=3;return rowForLevel(await dictionary.reading('いし')).words.includes('意志');}));
  // Every CPU meaning must obey both the grade and genre filters, with aligned images.
  const genreAudit=await page.evaluate(async()=>{
   ST.level=5;ST.cpuGenres=['animal'];
   const pool=getPool(await dictionary.prepare(poolHead(),ST.level,ST.cpuGenres));
   return {count:pool.length,valid:pool.every(r=>r.words.every((w,i)=>ShiritoriVocabulary.category(w,r.meanings[i],r.imagequeries[i]?.ja)==='animal')),invariant:pool.every(r=>r.words.length===r.meanings.length&&r.words.length===r.imagequeries.length)};
  });
  assert.ok(genreAudit.count>0&&genreAudit.valid&&genreAudit.invariant);
  assert.ok(await page.evaluate(async()=>{ST.tail='';ST.used.clear();const picks=[];for(let i=0;i<10;i++)picks.push(await cpuChoose());return picks.every(r=>r&&r.words.every((w,i)=>ShiritoriVocabulary.category(w,r.meanings[i],r.imagequeries[i]?.ja)==='animal'));}));
  assert.ok(await page.evaluate(()=>!!lookupRow('りんご')),'Player may use excluded genre');
  assert.equal(await page.evaluate(async()=>{ST.cpuGenres=[];return await cpuChoose();}),null);
  await page.evaluate(()=>{ST.level=1;ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);syncSettingsUI();});
  await page.screenshot({path:path.join(out,name+'-words.png'),fullPage:true});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  assert.ok(await page.evaluate(()=>{const e=document.querySelector('.lv-grid');return e.scrollWidth<=e.clientWidth;}),'All five levels fit the settings panel');
  await page.locator('[data-settings-tab="effects"]').click();
  assert.equal(await page.locator('#speechVolume').inputValue(),'100');
  assert.equal(await page.locator('#effectsVolume').inputValue(),'100');
  await page.locator('#speechVolume').fill('35');
  await page.locator('#effectsVolume').fill('65');
  assert.equal(await page.locator('#speechVolumeValue').innerText(),'35%');
  assert.equal(await page.locator('#effectsVolumeValue').innerText(),'65%');
  assert.deepEqual(await page.evaluate(()=>{
    const s=JSON.parse(localStorage.getItem('shiri-settings'));
    return [s.speechVolume,s.effectsVolume,s.voice];
  }),[.35,.65,false],'Volumes save independently without turning sound on');
  await page.locator('#speechVolume').focus();await page.keyboard.press('ArrowRight');
  assert.equal(await page.locator('#speechVolumeValue').innerText(),'36%','Keyboard adjusts the slider');
  if(name==='desktop'){
   const audioChecks=await page.evaluate(async()=>{
    ST.voice=true;
    const synth=window.speechSynthesis,originalSpeak=synth.speak,originalCancel=synth.cancel;
    const volumes=[];
    synth.speak=u=>{volumes.push(u.volume);queueMicrotask(()=>u.onend?.());};synth.cancel=()=>{};
    try{
     speak('ことば');await speakAsync('せつめい');
     setAudioVolume('speechVolume',0);speak('むおん');await speakAsync('むおん');
    }finally{synth.speak=originalSpeak;synth.cancel=originalCancel;}
    setAudioVolume('speechVolume',36);
    // Capture the actual media-element volume passed to recorded voice playback.
    const OriginalAudio=window.Audio;let fileVolume;
    window.Audio=class{addEventListener(){}play(){fileVolume=this.volume;return Promise.reject(new Error('fixture'));}};
    try{await playSound('hiragana.wav');}finally{window.Audio=OriginalAudio;}
    await robotLink.warmSound();robotLink.sound('lock');
    const effectsGain=robotLink.mix.gain.value;
    setAudioVolume('effectsVolume',0);const silentGain=robotLink.mix.gain.value;
    setAudioVolume('effectsVolume',65);ST.voice=false;robotLink.mute();saveSettings();
    return {volumes,fileVolume,effectsGain,silentGain};
   });
   assert.equal(audioChecks.volumes.length,2,'Zero skips speech');
   assert.ok(audioChecks.volumes.every(v=>Math.abs(v-.36)<.00001),'Both speech paths use reading volume');
   assert.equal(audioChecks.fileVolume,.36,'Recorded guidance uses reading volume');
   assert.ok(Math.abs(audioChecks.effectsGain-.85*.65)<.00001,'Effects use independent gain');
   assert.equal(audioChecks.silentGain,0,'Zero silences effects');
  }
  await page.screenshot({path:path.join(out,name+'-audio.png'),fullPage:true});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Audio settings fit screen');
  assert.equal(await page.locator('#inputHint').isVisible(),true);
  assert.match(await page.locator('#inputHint').innerText(),/VOICEVOX:ずんだもん/);
  assert.equal(await page.locator('#pageGame #inputHint').count(),0);
  await page.locator('#togSkipLink').click();
  assert.equal(await page.evaluate(()=>ST.skipLinkAnimation),true);
  if(name==='desktop'){
   assert.deepEqual(await page.evaluate(()=>{
    const saved=localStorage.getItem('shiri-settings');
    const cases=[{}, {speechVolume:0,effectsVolume:0}, {speechVolume:-1,effectsVolume:4}, {speechVolume:null,effectsVolume:'bad'}];
    const result=cases.map(s=>{localStorage.setItem('shiri-settings',JSON.stringify(s));loadSettings();return [ST.speechVolume,ST.effectsVolume];});
    localStorage.setItem('shiri-settings',saved);loadSettings();return result;
   }),[[1,1],[0,0],[0,1],[1,1]],'Old settings, zero and invalid volumes load safely');
  }
  if(name==='desktop'){
   assert.deepEqual(await page.evaluate(()=>{
    const saved=localStorage.getItem('shiri-settings');
    const results=[1,2,3].map(level=>{localStorage.setItem('shiri-settings',JSON.stringify({level}));loadSettings();return ST.level;});
    localStorage.setItem('shiri-settings',saved);loadSettings();return results;
   }),[1,3,5],'Legacy settings migrate to grade bands');
  }
  await page.reload();await page.waitForFunction(()=>ST.wlLoaded);
  await page.locator('#noticeStart').click();
  assert.deepEqual(await page.evaluate(()=>[ST.speechVolume,ST.effectsVolume,ST.voice]),[.36,.65,false],'Volumes persist on reload');
  await page.evaluate(()=>{toggleVoice();toggleVoice();});
  assert.deepEqual(await page.evaluate(()=>[ST.speechVolume,ST.effectsVolume,ST.voice]),[.36,.65,false],'Master sound switch preserves both volumes');
  assert.equal(await page.evaluate(()=>ST.skipLinkAnimation),true);
  await page.evaluate(async()=>{await launchGame();switchIn('kbd');resetGame(false);showPage('game');window.aiCalls=0;validateWithAI=async()=>{window.aiCalls++;return {ok:false,safe:false};};});
  await page.evaluate(async()=>{setCurrentInput('りんこ');await submitWord();});
  assert.equal(await page.evaluate(()=>aiCalls),0);
  assert.ok(await page.locator('#wordSuggestions').isVisible());
  assert.ok(await page.locator('#wordSuggestions').innerText().then(t=>t.includes('りんご')));
  await page.screenshot({path:path.join(out,name+'-suggestions.png'),fullPage:true});
  await page.locator('#wordSuggestions button').filter({hasText:'りんご'}).click();
  assert.equal(await page.evaluate(()=>ST.currentInput),'りんご');
  assert.equal(await page.evaluate(()=>ST.history.length),0,'Correction requires explicit confirmation');
  if(width<=768)await page.evaluate(()=>switchMobTab('center'));
  await page.evaluate(async()=>{setCurrentInput('りんこ');await submitWord();});
  await page.locator('#wordSuggestions button').filter({hasText:'AIに'}).click();
  await page.waitForFunction(()=>aiCalls===1&&!ST.cpuBusy);
  assert.equal(await page.evaluate(()=>ST.history.length),0);
  await page.evaluate(async()=>{setCurrentInput('りんこ');await submitWord();resetGame(false);});
  assert.equal(await page.locator('#wordSuggestions').count(),0);
  if(name==='desktop'){
   assert.equal(await page.evaluate(async()=>{
    validateWithAI=async()=>({ok:true,safe:true,word:'あああああ',meaning:'確認済みのテスト語。',level:1});
    setCurrentInput('あああああ');ST.suggestionBypass=ST.currentInput;await submitWord();
    const row=ST.whitelist.find(r=>r.reading==='あああああ');
    const safe=row?.level===4&&!getPool().some(r=>r.reading==='あああああ');resetGame(false);return safe;
   }),true,'AI-estimated level cannot enlarge lower grade bands');
  }
  // Skip waits no mechanical animation, still draws the completed connection.
  const link=await page.evaluate(async()=>{
   ST.skipLinkAnimation=true;await commitWord('あなた','しりとり',lookupRow('しりとり'));
   const start=performance.now();await commitWord('CPU','りす',lookupRow('りす'));
   return {elapsed:performance.now()-start,nodes:document.querySelectorAll('.link-node').length,phase:document.querySelector('.rl-bridge')?.dataset.phase};
  });
  assert.equal(link.nodes,2);assert.equal(link.phase,'complete');assert.ok(link.elapsed<1200,JSON.stringify(link));
  assert.deepEqual(errors,[]);console.log(JSON.stringify({name,counts,genreAudit,link}));await page.close();
 }
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(()=>server.close());
