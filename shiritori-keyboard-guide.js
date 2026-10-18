/* Physical keystrokes drive an SVG demonstration, independently of Japanese IME text. */
const ShiritoriKeyboardGuide=(()=>{
  const ns='http://www.w3.org/2000/svg';
  let svg,hands,select,frame,visible='hands';
  const keys=new Map(),held=new Set(),fingers=[];
  const fingerNames=['左こゆび','左くすりゆび','左なかゆび','左ひとさしゆび','左おやゆび','右おやゆび','右ひとさしゆび','右なかゆび','右くすりゆび','右こゆび'];
  const mapping=['1QAZ`','2WSX','3EDC','4RFV5TGB','','','6YHN7UJM','8IK,','9OL.','0P;/-=[]\\'];
  const eventCode=e=>keys.has(e.code)?e.code:/^[a-z]$/i.test(e.key)?`Key${e.key.toUpperCase()}`:null;
  function node(tag,attrs,parent){const e=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))e.setAttribute(k,v);parent.append(e);return e;}
  function key(code,label,x,y,w=48,finger){
    const g=node('g',{class:'typing-key','data-code':code},svg);
    node('rect',{x,y,width:w,height:42,rx:6},g);
    const t=node('text',{x:x+w/2,y:y+27},g);t.textContent=label;
    keys.set(code,{g,label,x:x+w/2,y:y+22,finger});
    if(code==='KeyF'||code==='KeyJ')node('line',{x1:x+w/2-7,x2:x+w/2+7,y1:y+35,y2:y+35,stroke:'#1affa0','stroke-width':3},g);
  }
  function drawFinger(f){
    f.path.setAttribute('d',`M ${f.base[0]} ${f.base[1]} Q ${f.base[0]} ${f.y+70} ${f.x} ${f.y}`);
  }
  function animate(){
    cancelAnimationFrame(frame);
    const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
    const tick=()=>{
      let moving=false;
      fingers.forEach((f,i)=>{
        const active=[...held].reverse().map(c=>keys.get(c)).find(k=>k?.finger===i);
        const target=active?[active.x,active.y]:f.home;
        f.path.classList.toggle('active',!!active);
        const distance=Math.abs(f.x-target[0])+Math.abs(f.y-target[1]);
        if(distance>.5){f.x=reduced?target[0]:f.x+(target[0]-f.x)*.42;f.y=reduced?target[1]:f.y+(target[1]-f.y)*.42;moving=true;}
        drawFinger(f);
      });
      if(moving&&!reduced)frame=requestAnimationFrame(tick);
    };tick();
  }
  function clear(){held.clear();keys.forEach(k=>k.g.classList.remove('pressed'));if(fingers.length)animate();}
  function update(){
    const kbd=ST.inputMode==='kbd';document.body.classList.toggle('keyboard-input',kbd);
    document.getElementById('keyboardGuide').hidden=!kbd;
    if(!svg)return;
    svg.hidden=visible==='off';svg.style.display=visible==='off'?'none':'block';
    hands.style.display=visible==='hands'?'':'none';
    svg.setAttribute('viewBox',visible==='hands'?'0 0 800 425':'0 0 800 265');
    clear();
  }
  function init(){
    const root=document.getElementById('keyboardGuide');
    root.innerHTML='<div class="keyboard-guide-tools"><strong>⌨ キーボードのおてほん</strong><label>表示 <select id="typingDisplay"><option value="hands">キーと おてほんの手</option><option value="keys">キーだけ</option><option value="off">かくす</option></select></label></div><p id="typingAction" aria-live="off">FとJに ひとさしゆびを おこう。</p><p id="typingHelp">パソコンのキーボードを押すと光るよ。手はおてほんの動きです。日本語キーボードの英字配列を表示しています。</p>';
    select=document.getElementById('typingDisplay');
    try{const saved=localStorage.getItem('shiri-typing-guide');if(['hands','keys','off'].includes(saved))visible=saved;}catch{}
    select.value=visible;select.onchange=()=>{visible=select.value;try{localStorage.setItem('shiri-typing-guide',visible);}catch{}update();};
    svg=node('svg',{id:'typingSvg',viewBox:'0 0 800 425',role:'img','aria-label':'QWERTY配列と、おてほんの指の動き'},root);
    const rows=[['1234567890-^',50,10],['QWERTYUIOP@[',75,60],['ASDFGHJKL;:',90,110],['ZXCVBNM,./',115,160]];
    rows.forEach(([letters,start,y],r)=>[...letters].forEach((ch,i)=>{
      const code=/[A-Z]/.test(ch)?`Key${ch}`:/[0-9]/.test(ch)?`Digit${ch}`:({'-':'Minus','^':'Equal','@':'BracketLeft','[':'BracketRight',';':'Semicolon',':':'Quote',',':'Comma','.':'Period','/':'Slash'})[ch];
      const finger=mapping.findIndex(chars=>chars.includes(ch));key(code,ch,start+i*50,y,46,finger<0?9:finger);
    }));
    key('Backspace','⌫',700,10,90,9);key('Enter','Enter',700,60,90,9);
    key('ShiftLeft','Shift',10,160,95,0);key('ShiftRight','Shift',625,160,115,9);
    key('Space','スペース',225,210,350,5);
    hands=node('g',{class:'typing-hands'},svg);
    node('path',{class:'palm',d:'M 155 405 Q 140 350 155 320 Q 205 290 288 319 L 322 358 Q 315 390 290 410 Z'},hands);
    node('path',{class:'palm',d:'M 645 405 Q 660 350 645 320 Q 595 290 512 319 L 478 358 Q 485 390 510 410 Z'},hands);
    const homes=['KeyA','KeyS','KeyD','KeyF',null,'Space','KeyJ','KeyK','KeyL','Semicolon'];
    const bases=[[163,340],[193,325],[228,320],[264,330],[290,355],[510,355],[536,330],[572,320],[607,325],[637,340]];
    homes.forEach((code,i)=>{
      const k=keys.get(code),home=k?[k.x,k.y]:[340,232];
      const path=node('path',{class:'typing-finger','data-finger':i},hands);
      const f={path,home,base:bases[i],x:home[0],y:home[1]};fingers.push(f);drawFinger(f);
    });
    // Keep legends readable through the translucent hands.
    const labels=node('g',{class:'typing-labels'},svg);
    keys.forEach(k=>{const t=node('text',{x:k.x,y:k.y+5},labels);t.textContent=k.label;});
    document.addEventListener('keydown',e=>{
      if(ST.inputMode!=='kbd'||e.target.id!=='kbdInput'||ST.cpuBusy||ST.gameOver)return;
      const code=eventCode(e);
      const k=keys.get(code);if(!k)return;
      held.add(code);k.g.classList.add('pressed');animate();
      document.getElementById('typingAction').textContent=`${k.label} → ${fingerNames[k.finger]}`;
    },true);
    document.addEventListener('keyup',e=>{const code=eventCode(e);held.delete(code);keys.get(code)?.g.classList.remove('pressed');animate();});
    window.addEventListener('blur',clear);document.getElementById('kbdInput').addEventListener('blur',clear);
    document.addEventListener('visibilitychange',clear);update();
  }
  return {init,update,clear};
})();
