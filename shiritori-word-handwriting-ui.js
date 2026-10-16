/* Adapter to the existing canvas/model. Legacy one-character input stays independent. */
const WordHandwritingUI=(()=>{
  let results=[],selected=0,editing=-1,busy=false,initialized=false,pickerOpen=false,singleLabel=null;
  const $=id=>document.getElementById(id);
  const engine=()=>ShiritoriWordHandwriting;
  const active=()=>ST.handwritingMode==='word'&&ST.charMode==='hiragana';
  function sync(){
    if(!initialized){
      initialized=true;
      $('btnReadWord').onclick=()=>runPredict();
      $('btnAcceptWord').onclick=accept;
      $('btnWordSmall').onclick=()=>{
        const item=results[selected]?.chars[editing];if(!item)return;
        const e=engine();edit(e.smallMap[item.ch]||e.largeMap[item.ch]||item.ch);
      };
      $('btnWordOther').onclick=()=>{pickerOpen=!pickerOpen;render();};
      $('enableWordHandwriting').onchange=()=>setMode($('enableWordHandwriting').checked?'word':'single');
    }
    $('wordHandwriting').classList.toggle('hidden',!active());
    $('predRow').classList.toggle('hidden',active());
    $('canvasAux').classList.toggle('hidden',active());
    $('wordKatakanaNote').classList.toggle('hidden',ST.charMode==='hiragana');
    $('modeCanvas').classList.toggle('word-handwriting',active());
    $('enableWordHandwriting').checked=ST.handwritingMode==='word';
    render();
  }
  function setMode(mode){
    if(!['single','word'].includes(mode)||mode===ST.handwritingMode)return;
    ST.handwritingMode=mode;clearCV(true);saveSettings();sync();resizeCV();
  }
  function invalidate(){
    HandwritingReview.reset();
    results=[];selected=0;editing=-1;busy=false;pickerOpen=false;singleLabel=null;
    if(initialized)render();
  }
  function render(){
    if(!initialized)return;
    const holder=$('wordResults');holder.replaceChildren();
    const row=$('wordCharacters');row.replaceChildren();
    const choices=$('wordCharacterChoices');choices.replaceChildren();
    $('btnReadWord').disabled=busy||!tfModel||!ST.strokes.length;
    $('btnAcceptWord').disabled=busy||!results.length;
    $('wordStatus').textContent=busy?'よみとり中…':results.length?'ちがう もじは、おして なおせるよ。':'ひだりから ことばを かいてね。手を とめると 自動で よみとるよ。小さい字は 小さめに。';
    results.forEach((r,i)=>{
      const b=document.createElement('button');b.type='button';b.className='word-candidate';
      b.textContent=r.chars.map(c=>c.ch).join('');b.setAttribute('aria-pressed',String(i===selected));
      b.onclick=()=>{selected=i;editing=-1;pickerOpen=false;render();};holder.appendChild(b);
    });
    results[selected]?.chars.forEach((c,i)=>{
      const b=document.createElement('button');b.type='button';b.className='word-character';b.textContent=c.ch;
      b.dataset.index=String(i+1);
      b.style.setProperty('--segment-color',color(i));
      b.setAttribute('aria-label',`${i+1}もじめ「${c.ch}」をなおす`);b.setAttribute('aria-pressed',String(i===editing));
      b.onclick=()=>{editing=i;pickerOpen=false;render();};row.appendChild(b);
    });
    const item=results[selected]?.chars[editing];
    $('wordCorrection').classList.toggle('hidden',!item);
    if(item){
      const offered=[...new Set(item.choices.map(c=>c.ch))];
      offered.forEach(ch=>{
        const b=document.createElement('button');b.type='button';b.className='word-character';b.textContent=ch;
        b.setAttribute('aria-label',`${editing+1}もじめを「${ch}」にする`);
        b.onclick=()=>edit(ch);choices.appendChild(b);
      });
      const e=engine();$('btnWordSmall').disabled=!(e.smallMap[item.ch]||e.largeMap[item.ch]);
    }
    $('wordKanaPicker').hidden=!item||!pickerOpen;
    $('btnWordOther').setAttribute('aria-expanded',String(!!item&&pickerOpen));
    $('wordKanaPicker').replaceChildren();
    if(item&&pickerOpen)for(const ch of [...LABELS_HIRAGANA,...Object.values(engine().smallMap),'ー']){
      const b=document.createElement('button');b.type='button';b.textContent=ch;b.className='word-character';
      b.setAttribute('aria-label',`${editing+1}もじめを「${ch}」にする`);b.onclick=()=>{pickerOpen=false;edit(ch);};$('wordKanaPicker').appendChild(b);
    }
    const chars=active()?results[selected]?.chars:singleLabel&&ST.strokes.length?[{ch:singleLabel,segment:{box:engine().bounds(ST.strokes),strokes:ST.strokes}}]:[];
    renderBounds(chars||[]);
    HandwritingReview.update(chars||[],active()?editing:0);
  }
  const color=i=>['#1765cd','#7c3aed','#a64b00','#087c6c','#b82d70'][i%5];
  function renderBounds(chars){
    const svg=$('handwritingBounds');svg.replaceChildren();
    $('wordBoundsHint').hidden=!active()||!chars.length;
    svg.setAttribute('viewBox',`0 0 ${cv.width} ${cv.height}`);
    if(!chars.length)return;
    const display=cv.getBoundingClientRect();
    const ratio=cv.width/(display.width||cv.width),ratioY=cv.height/(display.height||cv.height);
    const node=(tag,attrs)=>{
      const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
      for(const [key,value] of Object.entries(attrs))n.setAttribute(key,String(value));return n;
    };
    chars.forEach((item,i)=>{
      const b=item.segment.box,padding=2*ratio+Math.max(0,...item.segment.strokes.map(s=>(s.lineWidth||0)/2));
      const x=Math.max(ratio,b.l-padding),y=Math.max(ratio,b.t-padding);
      const w=Math.max(ratio,Math.min(cv.width-ratio,b.r+padding)-x),h=Math.max(ratio,Math.min(cv.height-ratio,b.b+padding)-y);
      const group=node('g',{'data-segment':i+1,'data-character':item.ch,'class':active()&&editing===i?'selected':''});
      const rect=node('rect',{x,y,width:w,height:h,rx:3*ratio,stroke:color(i),'class':'handwriting-box','vector-effect':'non-scaling-stroke'});
      group.appendChild(rect);
      const text=`${i+1}: ${item.ch}`,labelW=Math.min(cv.width-2*ratio,(text.length*9+8)*ratio),labelH=21*ratioY;
      const labelX=Math.max(ratio,Math.min(x,cv.width-labelW-ratio));
      const labelY=Math.max(ratio,Math.min(y>=labelH?y-labelH:y,cv.height-labelH-ratio));
      group.appendChild(node('rect',{x:labelX,y:labelY,width:labelW,height:labelH,rx:3*ratio,fill:'#fff',stroke:color(i),'vector-effect':'non-scaling-stroke'}));
      const label=node('text',{x:labelX/ratio+4,y:labelY/ratioY+15,transform:`scale(${ratio} ${ratioY})`,fill:color(i),'font-size':14,'font-weight':700});
      label.textContent=text;group.appendChild(label);svg.appendChild(group);
    });
  }
  function singleBounds(ch){singleLabel=ch;if(initialized&&!active())render();}
  function edit(ch){
    const candidate=results[selected];if(!candidate||editing<0)return;
    // Beam paths share immutable prefixes; editing must affect only this candidate.
    candidate.chars=candidate.chars.map((c,i)=>i===editing?{...c,ch}:c);render();
  }
  function rasterize(segment){
    // Re-render from coordinates: display pen width and guides never enter recognition.
    const c=document.createElement('canvas');c.width=c.height=64;
    const ctx=c.getContext('2d',{willReadFrequently:true}),b=segment.box;
    const scale=52/Math.max(b.w,b.h),ox=(64-b.w*scale)/2,oy=(64-b.h*scale)/2;
    ctx.fillStyle='#000';ctx.fillRect(0,0,64,64);ctx.strokeStyle=ctx.fillStyle='#fff';
    ctx.lineWidth=3;ctx.lineCap=ctx.lineJoin='round';
    for(const s of segment.strokes){
      const pts=s.points.map(p=>({x:ox+(p.x-b.l)*scale,y:oy+(p.y-b.t)*scale}));
      ctx.beginPath();ctx.arc(pts[0].x,pts[0].y,1.5,0,Math.PI*2);ctx.fill();
      ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);for(const p of pts.slice(1))ctx.lineTo(p.x,p.y);ctx.stroke();
    }
    const pixels=ctx.getImageData(0,0,64,64).data;
    return Float32Array.from({length:4096},(_,i)=>pixels[i*4]/255);
  }
  async function predict(){
    if(busy||!active()||ST.inputMode!=='canvas'||!tfModel||drawing||!ST.strokes.length)return;
    clearTimeout(predTimer);
    const revision=predRevision,model=tfModel,labels=LABELS;
    const valid=()=>revision===predRevision&&model===tfModel&&labels===LABELS&&active()&&ST.inputMode==='canvas'&&!drawing;
    busy=true;render();
    try{
      const plan=engine().plan(ST.strokes),predictions=[];
      // Small batches yield to drawing and avoid a large tensor on school devices.
      for(let offset=0;offset<plan.segments.length;offset+=12){
        if(!valid())return;
        const batch=plan.segments.slice(offset,offset+12),data=new Float32Array(batch.length*4096);
        batch.forEach((s,i)=>data.set(rasterize(s),i*4096));
        let input,output;
        try{
          input=tf.tensor4d(data,[batch.length,64,64,1]);output=model.predict(input);
          const values=await output.data();
          if(values.length!==batch.length*labels.length)throw Error('model-output');
          batch.forEach((s,i)=>predictions.push(labels.map((ch,j)=>({ch,p:values[i*labels.length+j]})).sort((a,b)=>b.p-a.p).slice(0,4)));
        }finally{output?.dispose();input?.dispose();}
        await new Promise(resolve=>setTimeout(resolve,0));
      }
      if(!valid())return;
      results=engine().decode(plan,predictions);selected=0;editing=-1;busy=false;render();
      if(!results.length)$('wordStatus').textContent='よめなかったよ。もじの あいだを 少し あけてみてね。';
    }catch(error){
      if(!valid())return;
      busy=false;render();
      $('wordStatus').textContent=error.message==='too-many-strokes'?'１つの ことばずつ かいてね。けして、もういちど。':'よみとれませんでした。もういちど「よみとる」を おしてね。';
      console.warn('word handwriting',error);
    }
  }
  function accept(){
    if(busy||!active()||!results[selected])return;
    setCurrentInput(ST.currentInput+results[selected].chars.map(c=>c.ch).join(''));
    clearCV(true);
  }
  return {active,sync,invalidate,predict,rasterize,setMode,refresh:render,singleBounds};
})();
