/* Optional speech input, selected in settings and remembered for shared-device players. No audio is stored by this app. */
const ShiritoriSpeech = (()=>{
  const $=id=>document.getElementById(id);
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  let epoch=0,recognizer=null,utterance=null,timer=null,running=false,paused=false;
  let candidate='',phase='word',misses=0,lexicon=null,lexiconTask=null,lastRound=-1,submitting=null;
  const clean=s=>String(s).normalize('NFKC').replace(/[\s。、，,.！？!?「」『』]/g,'').toLowerCase();
  const kana=s=>clean(s).replace(/[ァ-ヶ]/g,c=>String.fromCharCode(c.charCodeAt(0)-0x60));
  const supported=()=>!!(Recognition&&window.speechSynthesis&&window.SpeechSynthesisUtterance);
  function status(text){$('speechStatus').textContent=text;}
  function available(){
    return ST.inputMode==='speech'&&!document.hidden&&$('pageGame').classList.contains('active')&&
      !$('titleScreen')&&!document.querySelector('dialog[open]')&&!ST.cpuBusy&&!ST.packBusy&&
      !ST.demoRunning&&!ST.moderationLocked&&ST.wlLoaded&&ST.voice&&ST.speechVolume>0;
  }
  function valid(id){return id===epoch&&running&&!paused&&available();}
  function cancel(){
    epoch++;clearTimeout(timer);timer=null;
    const old=recognizer;recognizer=null;if(old){old.onend=old.onresult=old.onerror=null;try{old.abort();}catch{}}
    if(utterance){utterance.onend=utterance.onerror=null;utterance=null;window.speechSynthesis.cancel();}
    running=false;
  }
  function pause(message='おやすみ中。「きくのを さいかい」で つづけるよ。'){
    cancel();paused=true;candidate='';$('speechReading').textContent='';status(message);
    $('speechResume').hidden=false;$('speechPause').hidden=true;
  }
  function invalidate(){cancel();candidate='';phase='word';$('speechReading').textContent='';}
  function say(text,id){
    status(text);
    return new Promise(resolve=>{
      if(!valid(id)){resolve(false);return;}
      const u=new SpeechSynthesisUtterance(text);utterance=u;u.lang='ja-JP';u.volume=ST.speechVolume;
      let done=false,speechTimer;
      const finish=ok=>{if(done)return;done=true;clearTimeout(speechTimer);if(utterance===u)utterance=null;resolve(ok&&valid(id));};
      u.onend=()=>finish(true);u.onerror=()=>{if(done||!valid(id)||utterance!==u)return;finish(false);pause('読み上げが とまりました。音を たしかめて「きくのを さいかい」を おしてね。');};
      speechTimer=setTimeout(()=>{if(!valid(id)||utterance!==u)return;finish(false);pause('読み上げが とまりました。「きくのを さいかい」を おしてね。');},15000);timer=speechTimer;
      window.speechSynthesis.speak(u);
    });
  }
  async function prompt(text,id){
    if(!await say(text,id))return;
    // Give loudspeaker echo a short time to decay before opening the microphone.
    timer=setTimeout(()=>{if(valid(id))listen(id);},450);
  }
  async function readings(transcript){
    const value=kana(transcript);
    if(!value||value.length>80)return [];
    if(/^[ぁ-ゖー]+$/.test(value))return [value];
    if(!lexicon){
      if(!lexiconTask)lexiconTask=(async()=>{
        const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
        try{const r=await fetch('./data/shiritori-speech-readings.json',{signal:controller.signal});if(!r.ok)throw Error('readings');return await r.json();}
        finally{clearTimeout(timeout);}
      })().finally(()=>{lexiconTask=null;});
      lexicon=await lexiconTask;
    }
    // Prefer the whole spelling, including its ambiguous readings.
    if(lexicon[value])return lexicon[value].filter(n=>dictionary.lookup(n));
    // Recognition can mix kanji and kana within a compound. Join partial readings,
    // but accept only complete dictionary words, never a guessed shiritori tail.
    const paths=Array.from({length:value.length+1},()=>new Set());
    paths[0].add('');let states=1;
    for(let start=0;start<value.length;start++){
      if(!paths[start].size)continue;
      const parts=[];
      if(/^[ぁ-ゖー]$/.test(value[start]))parts.push([start+1,[value[start]]]);
      for(let end=start+1;end<=value.length;end++){
        const part=value.slice(start,end);
        if(!/^[ぁ-ゖー]+$/.test(part)&&lexicon[part])parts.push([end,lexicon[part]]);
      }
      for(const [end,readings] of parts)for(const prefix of paths[start])for(const reading of readings){
        const joined=prefix+reading;
        if(joined.length>80||paths[end].has(joined))continue;
        // Do not truncate alternatives and silently choose a reading on overflow.
        if(++states>2048)return [];
        paths[end].add(joined);
      }
    }
    return [...paths[value.length]].filter(n=>dictionary.lookup(n)).sort();
  }
  async function received(texts,id){
    const text=texts[0];
    if(!valid(id))return;
    const command=kana(text);
    if(command==='おやすみ'||command==='すとっぷ'){pause();return;}
    if(phase==='replay'){
      if(/^(もういっかい|もう一回|もういちど)$/.test(command)){
        invalidate();resetGame(false);
        setStatus('ready','こえで ことばを つなげよう。','もじと よみあげを たしかめてね。');tick();
      }else await prompt('もういっかい、と いうと、さいしょから あそべるよ。おやすみ、で とまるよ。',id);
      return;
    }
    if(phase==='confirm'){
      if(/^(ok|okay|おーけー|おおけえ|おっけー|おっけい|おーけい|はい)$/.test(command)){
        await connectCandidate(id);
        return;
      }
      if(/^(ちがうよ|違うよ|ちがう|違う|いいえ|やりなおし)$/.test(command)){
        candidate='';phase='word';$('speechReading').textContent='';setCurrentInput('');
        await prompt('もういちど、しゃべってください。',id);return;
      }
      await prompt(candidate+' と認識。よければ オーケー、ちがえば ちがうよ、と いってね。',id);return;
    }
    status('ひらがなの よみを たしかめています…');
    let choices;
    try{choices=[...new Set((await Promise.all(texts.map(readings))).flat())];}catch{choices=[];}
    if(!valid(id))return;
    if(choices.length>1){
      // Preserve recognition order when multiple legal readings share the head.
      const next=choices.find(n=>dictionary.lookup(n)&&!ST.used.has(norm(n))&&(!ST.tail||firstChar(n)===ST.tail));
      if(next){await acceptReading(next,id,true);return;}
      await prompt(ST.tail?'「'+displayStr(ST.tail)+'」から はじまる、まだ つかっていない ことばを しゃべってね。':'まだ つかっていない ことばを しゃべってね。',id);return;
    }
    if(choices.length!==1){
      await prompt('よみかたを ひとつに できませんでした。もういちど、ひらがなを いちもじずつ つなげて、しゃべってください。',id);return;
    }
    await acceptReading(choices[0],id);
  }
  async function acceptReading(reading,id,automatic=false){
    if(!valid(id))return;
    candidate=reading;setCurrentInput(candidate);$('speechReading').textContent=displayStr(candidate);
    if(automatic||!ST.speechConfirm){await connectCandidate(id);return;}
    phase='confirm';
    await prompt(candidate+' と認識。よければ オーケー、ちがえば ちがうよ、と いってね。',id);
  }
  async function connectCandidate(id){
    if(!valid(id)||!candidate)return;
    const word=candidate;candidate='';phase='word';status('ことばを つないでいます。');
    setCurrentInput(word);
    // Submit the spoken reading through the existing game rules without a tap-only suggestion panel.
    ST.suggestionBypass=word;
    const before=ST.history.length;
    submitting=id;
    try{await submitWord();}finally{if(submitting===id)submitting=null;}
    if(!valid(id))return;
    if(ST.history.length===before&&!ST.gameOver){
      await prompt(($('scMain').textContent||'この ことばは つかえません。')+'。もういちど、しゃべってください。',id);
    }else{running=false;tick();}
  }
  function syncOptionsUI(){
    $('speechPrompt').checked=ST.speechPrompt;
    $('speechPromptLabel').textContent='入力を うながす 音声案内：'+(ST.speechPrompt?'オン':'オフ');
    $('speechConfirm').checked=ST.speechConfirm;
    $('speechConfirmLabel').textContent='聞き返し：'+(ST.speechConfirm?'オン':'オフ');
    $('speechInstructions').textContent=ST.speechConfirm?'「オーケー」で つなぐ ／「ちがうよ」で いいなおす':'ききとった ことばを、そのまま つなぐよ。';
  }
  function setOption(key,enabled){
    ST[key]=enabled;invalidate();
    if(ST.inputMode==='speech')setCurrentInput('');
    saveSettings();syncOptionsUI();
  }
  function listen(id){
    if(!valid(id))return;
    const r=new Recognition();recognizer=r;
    r.lang='ja-JP';r.continuous=false;r.interimResults=false;r.maxAlternatives=5;
    let texts=[''],failure='';const finalResults=new Map();
    r.onstart=()=>{if(valid(id))status(phase==='confirm'?'🎤「オーケー」か「ちがうよ」を どうぞ':phase==='replay'?'🎤「もういっかい」で あそぶよ':'🎤 きいているよ。ことばを ひとつ どうぞ');};
    r.onresult=e=>{
      if(!valid(id)||recognizer!==r)return;
      if(window.speechSynthesis.speaking||activeVoiceAudio.size){invalidate();return;}
      for(let i=e.resultIndex||0;i<e.results.length;i++)if(e.results[i].isFinal){
        finalResults.set(i,Array.from(e.results[i]).slice(0,5).map(a=>a.transcript).filter(Boolean));
      }
      texts=[''];
      for(const [,parts] of [...finalResults].sort((a,b)=>a[0]-b[0])){
        texts=[...new Set(texts.flatMap(prefix=>parts.map(part=>prefix+part)))].slice(0,5);
      }
    };
    r.onerror=e=>{
      failure=e.error||'unknown';
      if(valid(id)&&recognizer===r&&['not-allowed','service-not-allowed'].includes(failure))pause('マイクを つかえません。ブラウザの マイク許可を たしかめてね。');
    };
    r.onend=async()=>{
      if(!valid(id)||recognizer!==r)return;
      if(recognizer===r)recognizer=null;clearTimeout(timer);
      if(failure&&!['no-speech','aborted'].includes(failure)){
        pause(failure==='not-allowed'||failure==='service-not-allowed'?'マイクを つかえません。ブラウザの マイク許可を たしかめてね。':'音声入力に つながりません。通信や マイクを たしかめて「きくのを さいかい」を おしてね。');return;
      }
      if(!texts[0]){
        if(++misses>=3){pause('声が きこえなかったので おやすみ中。「きくのを さいかい」で つづけるよ。');return;}
        await prompt(phase==='confirm'?'オーケー か、ちがうよ、と いってね。':'もういちど、しゃべってください。',id);return;
      }
      misses=0;
      try{await received(texts,id);}catch{if(valid(id))pause('うまく つづけられませんでした。「きくのを さいかい」で ためしてね。');}
    };
    // Covers browsers that never dispatch onend after a device disconnect.
    timer=setTimeout(()=>{if(valid(id))pause('マイクが とまりました。「きくのを さいかい」で つづけるよ。');},20000);
    try{r.start();}catch{pause('マイクを はじめられません。「きくのを さいかい」を おしてね。');}
  }
  function tick(){
    if(lastRound!==ST.round){lastRound=ST.round;invalidate();}
    if(submitting===epoch)return;
    if(!available()){
      if(running)invalidate();
      if(ST.inputMode==='speech'&&(!ST.voice||ST.speechVolume===0))pause('音が オフです。「きくのを さいかい」で 音を オンにして つづけるよ。');
      return;
    }
    if(recognizer&&(window.speechSynthesis.speaking||activeVoiceAudio.size)){invalidate();return;}
    if(paused||running||window.speechSynthesis.speaking||activeVoiceAudio.size)return;
    if(ST.gameOver)hideReplayPopup();
    if(isMobile())switchMobTab('center');
    running=true;const id=++epoch;phase=ST.gameOver?'replay':'word';
    if(ST.gameOver||ST.speechPrompt){
      prompt(ST.gameOver?'おしまい。もういっかい、と いうと、さいしょから あそべるよ。':ST.tail?`「${ST.tail}」から はじまる ことばを しゃべってください。`:'ことばを ひとつ、しゃべってください。',id);
    }else{
      status(ST.tail?`「${displayStr(ST.tail)}」から はじまる ことばを どうぞ。`:'ことばを ひとつ どうぞ。');
      timer=setTimeout(()=>{if(valid(id))listen(id);},450);
    }
  }
  function resume(){
    if(ST.inputMode!=='speech')return;
    cancel();lastRound=ST.round;paused=false;misses=0;candidate='';phase='word';
    setCurrentInput('');$('speechReading').textContent='';
    ST.voice=true;if(ST.speechVolume===0)ST.speechVolume=.8;saveSettings();
    $('btnVoice').textContent='🔊 おと';$('btnVoice').classList.add('on');syncSettingsUI();
    $('speechResume').hidden=true;$('speechPause').hidden=false;tick();
  }
  function enter(){
    if(!supported()){$('speechHelp').textContent='このブラウザでは 音声入力を つかえません。てがき・ボタン・キーボードを つかってね。';return;}
    switchIn('speech');showPage('game');if(isMobile())switchMobTab('center');resume();
  }
  function init(){
    $('speechConfirm').onchange=e=>setOption('speechConfirm',e.target.checked);
    $('speechPrompt').onchange=e=>setOption('speechPrompt',e.target.checked);syncOptionsUI();
    $('speechEnter').onclick=enter;$('speechPause').onclick=()=>pause();$('speechResume').onclick=resume;
    if(!supported()){$('speechEnter').disabled=true;$('speechHelp').textContent='このブラウザは 音声入力に 対応していません。';}
    document.addEventListener('visibilitychange',()=>{if(document.hidden&&ST.inputMode==='speech')pause('画面を はなれたので おやすみ中。「きくのを さいかい」で つづけるよ。');});
    window.addEventListener('pagehide',()=>cancel());
    setInterval(tick,250);
  }
  return {init,enter,invalidate,tick,syncOptionsUI,supported};
})();
