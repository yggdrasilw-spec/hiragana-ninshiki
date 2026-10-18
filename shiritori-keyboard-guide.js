/* Physical keystrokes drive an SVG demonstration, independently of Japanese IME text. */
const ShiritoriKeyboardGuide=(()=>{
  const ns='http://www.w3.org/2000/svg';
  let svg,hands,select,frame,keySpotlight,visible='hands',composing=false,draftText='',draftValid=false;
  const keys=new Map(),held=new Set(),fingers=[],rigs=[];
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
    const [bx,by]=f.base,dx=f.x-bx,dy=f.y-by;
    // A curled finger has a short projection from the knuckle to its contact point.
    const bend=[bx+dx*.48,by+dy*.46],distal=[bx+dx*.86,by+dy*.78];
    f.path.setAttribute('d',`M ${bx} ${by} C ${bx+dx*.1} ${by+dy*.15} ${bend[0]} ${bend[1]+12} ${bend.join(' ')} S ${distal[0]} ${distal[1]+8} ${distal.join(' ')} Q ${f.x} ${f.y+8} ${f.x} ${f.y}`);
    const angle=Math.atan2(dy,dx)*180/Math.PI+90;
    (f.thumb?[distal]:[bend,distal]).forEach(([x,y],i)=>f.joints[i].setAttribute('transform',`translate(${x} ${y}) rotate(${angle})`));
    f.nail.setAttribute('transform',`translate(${f.x} ${f.y+4}) rotate(${angle})`);
  }
  function rotate(x,y,angle){const r=angle*Math.PI/180;return [x*Math.cos(r)-y*Math.sin(r),x*Math.sin(r)+y*Math.cos(r)];}
  function handPose(rig,active){
    const reaching=active.filter(k=>Math.floor(k.finger/5)===rig.side);
    if(!reaching.length)return {...rig.homePose};
    // For a chord, follow the largest reach and keep the other fingers on their keys.
    const key=reaching.reduce((best,k)=>{
      const f=fingers[k.finger],b=fingers[best.finger];
      return Math.hypot(k.x-f.home[0],k.y-f.home[1])>Math.hypot(best.x-b.home[0],best.y-b.home[1])?k:best;
    });
    const f=fingers[key.finger],dx=key.x-f.home[0],dy=key.y-f.home[1],distance=Math.hypot(dx,dy);
    const reach=Math.max(0,Math.min(1,(distance-45)/120));
    const share=.36+.46*reach,a=rig.homeAngle+Math.max(-10,Math.min(10,dx*.055));
    const [rx,ry]=rotate(f.rest[0]-rig.pivot[0],f.rest[1]-rig.pivot[1],a);
    // Compensate for rotation so the hand supplies most of a long reach.
    return {x:dx*share-(rx+rig.pivot[0]-f.home[0]),y:dy*share-(ry+rig.pivot[1]-f.home[1]),a};
  }
  function localPoint(rig,pose,x,y){
    const p=rotate(x-pose.x-rig.pivot[0],y-pose.y-rig.pivot[1],-pose.a);
    return [p[0]+rig.pivot[0],p[1]+rig.pivot[1]];
  }
  function animate(){
    cancelAnimationFrame(frame);
    const active=[...held].map(code=>keys.get(code)).filter(Boolean);
    const targets=rigs.map(rig=>handPose(rig,active));
    let last;
    const tick=time=>{
      const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
      const dt=last===undefined?16:Math.min(40,time-last);last=time;
      const blend=reduced?1:1-Math.exp(-dt/48);
      let moving=false;
      const approach=(value,target)=>{if(Math.abs(value-target)<.05||reduced)return target;moving=true;return value+(target-value)*blend;};
      rigs.forEach((rig,i)=>{
        const target=targets[i];
        for(const axis of ['x','y','a'])rig.pose[axis]=approach(rig.pose[axis],target[axis]);
        const p=rig.pose;rig.group.setAttribute('transform',`translate(${p.x} ${p.y}) rotate(${p.a} ${rig.pivot.join(' ')})`);
      });
      fingers.forEach((f,i)=>{
        const key=[...active].reverse().find(k=>k.finger===i),rig=rigs[Math.floor(i/5)];
        const target=key?localPoint(rig,targets[rig.side],key.x,key.y):f.rest;
        f.path.classList.toggle('active',!!key);
        f.x=approach(f.x,target[0]);f.y=approach(f.y,target[1]);
        drawFinger(f);
      });
      if(moving&&!reduced)frame=requestAnimationFrame(tick);
    };tick(performance.now());
  }
  function clear(){held.clear();composing=false;keys.forEach(k=>k.g.classList.remove('pressed'));if(fingers.length)animate();refresh();}
  function refresh(draft){
    if(draft){draftText=draft.text;draftValid=draft.valid;}
    const cue=document.getElementById('typingCue');if(!cue)return;
    keys.forEach(k=>k.g.classList.remove('hint-next','hint-edit'));
    let message='',key;
    if(ST.inputMode!=='kbd')return;
    if(ST.gameOver)message='もういちど あそぶときは「もういちど」を おしてね。';
    else if(ST.cpuBusy||ST.demoRunning||ST.moderationLocked)message='いまは まってね。';
    else if(composing)message='へんかん中だよ。Enterで よみを きめてから つなげよう。';
    else if(draftValid){message=`みどりに ひかる Enterキーを おして「${displayStr(draftText)}」を つなげよう。`;key='Enter';}
    else if(draftText&&(isEndWord(draftText)||ST.used.has(draftText)||(ST.tail&&firstChar(draftText)!==ST.tail))){
      const why=isEndWord(draftText)?'「ん」のつぎは つなげられないね。':ST.used.has(draftText)?'もう つかった ことばだよ。':`つぎは「${displayStr(ST.tail)}」からだよ。`;
      message=why+' きいろに ひかる Backspaceキーで １もじずつ けして なおそう。';key='Backspace';
    }else message=ST.tail?`つぎは「${displayStr(ST.tail)}」から。かきなおすときは Backspaceで けせるよ。`:'ことばを いれよう。かきなおすときは Backspaceで けせるよ。';
    const text=document.getElementById('typingCueText');if(text.textContent!==message)text.textContent=message;
    cue.dataset.action=key==='Enter'?'connect':key==='Backspace'?'edit':composing?'compose':'input';
    const cap=document.getElementById('typingCueKey');cap.hidden=!key;
    if(key){
      document.getElementById('typingCueKeyName').textContent=key==='Enter'?'Enter ↵':'Backspace ⌫';
      keys.get(key)?.g.classList.add(key==='Enter'?'hint-next':'hint-edit');
    }
    if(!held.size)document.getElementById('typingAction').textContent=key?`${key} → ${fingerNames[keys.get(key).finger]}`:'FとJに ひとさしゆびを おこう。';
    if(keySpotlight){
      keySpotlight.style.display=key?'':'none';
      if(key){
        const k=keys.get(key),rect=k.g.querySelector('rect');
        const box=keySpotlight.querySelector('rect');
        for(const attr of ['x','y','width','height'])box.setAttribute(attr,Number(rect.getAttribute(attr))+(['x','y'].includes(attr)?-3:6));
        const label=keySpotlight.querySelector('text');label.setAttribute('x',k.x);label.setAttribute('y',k.y+6);label.textContent=key==='Enter'?'Enter ↵':'⌫';
        keySpotlight.setAttribute('data-key',key);
      }
    }
  }
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
    root.innerHTML='<div class="keyboard-guide-tools"><strong>⌨ キーボードのおてほん</strong><label>表示 <select id="typingDisplay"><option value="hands">キーと おてほんの手</option><option value="keys">キーだけ</option><option value="off">かくす</option></select></label></div><p id="typingCue" role="status" aria-live="polite"><span id="typingCueKey" hidden><strong id="typingCueKeyName"></strong><small>ここを おす！</small></span><span id="typingCueText"></span></p><p id="typingAction" aria-live="off">FとJに ひとさしゆびを おこう。</p><p id="typingHelp">パソコンのキーボードを押すと光るよ。手はおてほんの動きです。日本語キーボードの英字配列を表示しています。</p>';
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
    const defs=node('defs',{},svg),gradient=node('linearGradient',{id:'typingFingerShade',x1:'0%',y1:'100%',x2:'0%',y2:'0%'},defs);
    [[0,'#a48bda'],[.45,'#d4c1fc'],[.72,'#b49be9'],[1,'#e0d0ff']].forEach(([offset,color])=>node('stop',{offset,'stop-color':color},gradient));
    const palms=[
      'M 115 197 Q 139 189 161 204 Q 188 193 211 205 Q 238 193 260 208 L 280 237 Q 300 249 290 274 Q 280 301 260 314 L 256 350 L 155 350 L 152 310 Q 113 283 115 197 Z',
      'M 565 197 Q 541 189 515 204 Q 488 193 465 205 Q 438 193 415 208 L 395 237 Q 375 249 385 274 Q 395 301 415 314 L 419 350 L 520 350 L 523 310 Q 562 283 565 197 Z'
    ];
    palms.forEach((d,side)=>{
      const group=node('g',{'data-hand':side===0?'left':'right'},hands);
      node('path',{class:'palm',d},group);
      const wristY=321;node('path',{class:'typing-wrist',d:side===0?`M 162 ${wristY} Q 205 333 255 ${wristY}`:`M 420 ${wristY} Q 465 333 514 ${wristY}`},group);
      const homeAngle=side===0?12:-12,pivot=[side===0?205:470,330],homePose={x:side===0?-24:24,y:0,a:homeAngle};
      group.setAttribute('transform',`translate(${homePose.x} 0) rotate(${homeAngle} ${pivot.join(' ')})`);
      rigs.push({side,group,pivot,homeAngle,homePose,pose:{...homePose}});
    });
    const homes=['KeyA','KeyS','KeyD','KeyF',null,'Space','KeyJ','KeyK','KeyL','Semicolon'];
    const bases=[[115,197],[161,204],[211,205],[260,208],[280,252],[395,252],[415,208],[465,205],[515,204],[565,197]];
    homes.forEach((code,i)=>{
      const k=keys.get(code),home=k?[k.x,k.y]:[340,232];
      const path=node('path',{class:'typing-finger','data-finger':i},rigs[Math.floor(i/5)].group);
      const thumb=i===4||i===5;
      const joints=Array.from({length:thumb?1:2},()=>node('path',{class:'typing-joint',d:'M -7 0 Q 0 -4 7 0'},rigs[Math.floor(i/5)].group));
      const nail=node('ellipse',{class:'typing-nail',rx:6,ry:4},rigs[Math.floor(i/5)].group);
      const rig=rigs[Math.floor(i/5)],rest=localPoint(rig,rig.pose,...home);
      const f={path,joints,nail,thumb,home,rest,base:bases[i],x:rest[0],y:rest[1]};fingers.push(f);drawFinger(f);
    });
    // Keep legends readable through the translucent hands.
    const labels=node('g',{class:'typing-labels'},svg);
    keys.forEach(k=>{const t=node('text',{x:k.x,y:k.y+5},labels);t.textContent=k.label;});
    // Draw the recommended key above the hands and legends so neither can hide it.
    keySpotlight=node('g',{id:'typingKeySpotlight','aria-hidden':'true'},svg);
    node('rect',{rx:9},keySpotlight);node('text',{},keySpotlight);keySpotlight.style.display='none';
    document.addEventListener('keydown',e=>{
      if(ST.inputMode!=='kbd'||e.target.id!=='kbdInput'||ST.cpuBusy||ST.gameOver)return;
      const code=eventCode(e);
      const k=keys.get(code);if(!k)return;
      held.add(code);k.g.classList.add('pressed');animate();
      document.getElementById('typingAction').textContent=`${k.label} → ${fingerNames[k.finger]}`;
    },true);
    document.addEventListener('keyup',e=>{const code=eventCode(e);held.delete(code);keys.get(code)?.g.classList.remove('pressed');animate();refresh();});
    window.addEventListener('blur',clear);document.getElementById('kbdInput').addEventListener('blur',clear);
    document.getElementById('kbdInput').addEventListener('compositionstart',()=>{composing=true;refresh();});
    document.getElementById('kbdInput').addEventListener('compositionend',()=>{composing=false;refresh();});
    document.addEventListener('visibilitychange',clear);update();
  }
  return {init,update,clear,refresh};
})();
