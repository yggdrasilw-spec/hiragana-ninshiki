/* Shared-device players. The original one-human vs CPU flow remains compatible. */
const ShiritoriPlayers = (()=>{
  const $=id=>document.getElementById(id);
  const marks=['●','▲','■','◆','★','♥','🤖'];
  const colors=['#71e6ff','#ffc778','#c5a5ff','#92ebaa','#ff9fbd','#e6e580','#ff6b8a'];
  let config={count:1,cpu:true,mode:'versus',names:[],inputs:[]};
  let players=[],index=0,waiting=false,result='';
  const enabled=()=>config.count>1||!config.cpu||config.mode==='coop';
  const current=()=>players[index];
  function persist(){try{localStorage.setItem('shiri-players-v1',JSON.stringify(config));}catch{}}
  function init(){
    try{
      const c=JSON.parse(localStorage.getItem('shiri-players-v1')||'null');
      if(c){config.count=Math.max(1,Math.min(6,Math.trunc(Number(c.count))||1));config.cpu=c.cpu!==false;config.mode=c.mode==='coop'?'coop':'versus';
        config.names=Array.isArray(c.names)?c.names.slice(0,6).map(n=>String(n).slice(0,16)):[];
        config.inputs=Array.isArray(c.inputs)?c.inputs.slice(0,6).map(m=>['canvas','btn','kbd'].includes(m)?m:'canvas'):[];}
    }catch{}
    if(config.count===1&&!config.cpu)config.mode='coop';
    $('btnPlayers').onclick=open;
    $('playerCount').onchange=names;
    $('playerSetupForm').onsubmit=e=>{e.preventDefault();apply();};
    $('cancelPlayers').onclick=()=>$('playerSetup').close();
    $('takeTurn').onclick=ready;
    $('restartPlayers').onclick=()=>{resetGame();};
    $('handoff').addEventListener('cancel',e=>e.preventDefault());
    $('giveUp').onclick=()=>{
      if(ST.cpuBusy||ST.gameOver||waiting)return;
      if(config.mode==='coop'){setStatus('ready','パスしました。','つぎの人が つづきを かんがえよう。');ST.cpuBusy=true;advance();}
      else eliminate('ギブアップ');
    };
    reset();
  }
  function names(){
    const count=Number($('playerCount').value),old=[...$('playerNames').querySelectorAll('input')].map(e=>e.value);
    $('playerNames').replaceChildren();
    for(let i=0;i<count;i++){
      const label=document.createElement('label');label.textContent=`${marks[i]} ${i+1}人目 `;
      const input=document.createElement('input');input.name=`player${i}`;input.maxLength=16;input.autocomplete='off';
      input.value=old[i]??config.names[i]??`プレイヤー${i+1}`;label.append(input);$('playerNames').append(label);
    }
  }
  function open(){
    $('playerCount').value=config.count;$('includeCpu').checked=config.cpu;$('playRule').value=config.mode;
    $('playerNames').replaceChildren();names();$('playerSetup').showModal();
  }
  function apply(){
    config.count=Number($('playerCount').value);config.cpu=$('includeCpu').checked;config.mode=$('playRule').value;
    config.names=[...$('playerNames').querySelectorAll('input')].map((e,i)=>e.value.trim()||`プレイヤー${i+1}`);
    if(config.count===1&&!config.cpu)config.mode='coop';
    persist();$('playerSetup').close();showPage('game');resetGame();
    setStatus('ready',`${current().name}さんから はじめよう。`,config.mode==='coop'?'みんなで 何語 つながるかな？':'「ん」・ギブアップで おやすみ。最後の１人が勝ち。');
  }
  function reset(){
    $('handoff').close();waiting=false;index=0;result='';
    players=Array.from({length:config.count},(_,i)=>({id:`human${i}`,name:config.names[i]||`プレイヤー${i+1}`,cpu:false,out:false,words:0,color:colors[i],mark:marks[i],input:config.inputs[i]||ST.inputMode}));
    if(config.cpu)players.push({id:'cpu',name:'CPU',cpu:true,out:false,words:0,color:colors[6],mark:marks[6]});
    render();
    if(enabled()&&current())switchIn(current().input);
  }
  function render(){
    const strip=$('playerStrip');strip.replaceChildren();
    document.body.classList.toggle('many-players',enabled());
    let turnChip;
    for(const [i,p] of players.entries()){
      const chip=document.createElement('div');chip.className='player-chip'+(p.out?' eliminated':'')+(i===index&&!ST.gameOver?' turn':'');
      chip.style.setProperty('--player-color',p.color);chip.textContent=`${p.mark} ${p.name}　${p.words}語${p.out?'（おやすみ）':i===index&&!ST.gameOver?'：いまのばん':''}`;
      if(i===index&&!ST.gameOver){chip.setAttribute('aria-current','step');turnChip=chip;}strip.append(chip);
    }
    if(turnChip){const left=turnChip.offsetLeft-strip.offsetLeft;if(left<strip.scrollLeft)strip.scrollLeft=left;else if(left+turnChip.offsetWidth>strip.scrollLeft+strip.clientWidth)strip.scrollLeft=left+turnChip.offsetWidth-strip.clientWidth;}
    $('giveUp').hidden=!enabled();$('giveUp').textContent=config.mode==='coop'?'パス':'ギブアップ';
    $('giveUp').disabled=ST.cpuBusy||ST.gameOver||waiting||!!current()?.cpu;
    $('playerRuleLabel').textContent=config.mode==='coop'?`みんなで ${ST.history.length}語`:'たいせん';
  }
  function rememberInput(mode){
    const p=current();if(!p||p.cpu||waiting)return;
    p.input=mode;const i=Number(p.id.slice(5));config.inputs[i]=mode;persist();
  }
  function committed(speaker,entry){
    const p=speaker==='CPU'?players.find(p=>p.cpu):current();if(!p)return;
    entry.playerId=p.id;entry.playerName=p.name;entry.playerColor=p.color;entry.playerMark=p.mark;
    p.words++;render();
  }
  function finish(text){
    result=text;waiting=false;ST.cpuBusy=false;ST.gameOver=true;
    $('handoff').close();render();updateWordBox(ST.currentInput);
    setStatus('win',text,`${ST.history.length}語 つながったよ！`);speak(text);showReplayPopup();
  }
  async function eliminate(reason){
    if(ST.gameOver||waiting)return;
    const p=current();p.out=true;ST.cpuBusy=true;
    setCurrentInput('');clearCV(true);renderPreds(null);
    const remaining=players.filter(p=>!p.out);
    if(remaining.length<=1){finish(remaining[0]?`${remaining[0].name}さんの かち！`:'ここまで つながったよ！');return;}
    await advance(`${p.name}さんは ${reason}で おやすみ。`);
  }
  async function advance(message=''){
    if(ST.gameOver)return;
    const round=ST.round;
    do{index=(index+1)%players.length;}while(current().out);
    ST.cpuBusy=true;render();
    if(current().cpu){await cpuTurn();return;}
    waiting=true;setCurrentInput('');clearCV(true);renderPreds(null);
    $('handoffTitle').textContent=`つぎは ${current().name}さん`;
    $('handoffMessage').textContent=[message,ST.tail?`「${displayStr(ST.tail)}」から つづけてね。`:'すきな ことばから はじめよう。'].filter(Boolean).join(' ');
    if(round!==ST.round)return;
    if(isMobile())switchMobTab('center');
    $('handoff').showModal();$('takeTurn').focus();
    speak(`つぎは ${current().name}さんです。`);
  }
  function ready(){
    if(!waiting||ST.gameOver)return;
    $('handoff').close();waiting=false;ST.cpuBusy=false;
    setCurrentInput('');switchIn(current().input);updateWordBox('');render();
    setStatus('ready',`${current().name}さんのばんです。`,ST.tail?`「${displayStr(ST.tail)}」から つづけよう。`:'すきな ことばを いれてね。');
  }
  async function ending(){
    if(config.mode==='coop'){
      ST.cpuBusy=false;setStatus('error','「ん」のつぎは つなげられないね。','ちがう ことばに なおして つづけよう。');updateWordBox(ST.currentInput);render();
    }else await eliminate('「ん」');
  }
  async function cpuTurn(){
    const round=ST.round;ST.cpuBusy=true;render();setStatus('thinking','CPUが かんがえています…','');
    await new Promise(r=>setTimeout(r,getCpuDelay()));if(round!==ST.round)return;
    const pick=await cpuChoose();
    if(round!==ST.round||pick===undefined)return;
    if(!pick||isEndWord(pick.reading)){
      if(config.mode==='coop'){
        // Keep the last valid tail and let humans continue after the CPU passes.
        await advance('CPUは パスしました。');
      }else await eliminate(pick?'「ん」':'ギブアップ');
      return;
    }
    await commitWord('CPU',pick.reading,pick,false);if(round!==ST.round)return;
    await advance();
  }
  function replayText(){return result?`${result} もういちど 同じメンバーで あそぼう。`:'同じメンバーで、さいしょの人から はじめよう。';}
  return {init,reset,render,open,enabled,current,committed,advance,ending,cpuTurn,rememberInput,replayText};
})();
