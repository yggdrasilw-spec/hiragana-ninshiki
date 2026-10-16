/* Observation only: chronological strokes/directions, never a correctness score. */
const HandwritingReview=(()=>{
  let initialized=false,characters=[],selected=-1,animation=0,playing=false,target=null;
  const $=id=>document.getElementById(id);
  const ns='http://www.w3.org/2000/svg';
  const palette=['#1765cd','#7c3aed','#a64b00','#087c6c','#b82d70'];
  function node(tag,attrs={},text){
    const el=document.createElementNS(ns,tag);
    for(const [key,value] of Object.entries(attrs))el.setAttribute(key,String(value));
    if(text!=null)el.textContent=text;return el;
  }
  function init(){
    if(initialized)return;initialized=true;
    const dialog=document.createElement('dialog');dialog.id='handwritingReviewDialog';
    dialog.setAttribute('aria-labelledby','handwritingReviewTitle');
    dialog.innerHTML='<h2 id="handwritingReviewTitle">かいた もじを みよう</h2><p>数字は この字の中で かいた順。矢印は かいた向きだよ。</p><svg id="characterReviewSvg" viewBox="0 0 340 280" role="img" aria-label="選んだ文字の筆跡・書いた順・向き"></svg><div class="handwriting-review-tools"><button type="button" id="btnCharacterReplay">▶ この字を 再生</button><button type="button" id="btnReviewClose">とじる</button></div><p id="characterReviewStatus" role="status" aria-live="polite"></p>';
    document.body.appendChild(dialog);
    $('btnProcessToggle').onclick=()=>setEnabled(!ST.showHandwritingProcess);
    $('showHandwritingProcess').onchange=e=>setEnabled(e.target.checked);
    $('btnStrokeReplay').onclick=()=>playing?cancel():replay(false);
    $('btnInspectCharacter').onclick=openCharacter;
    $('btnCharacterReplay').onclick=()=>playing?cancel():replay(true);
    $('btnReviewClose').onclick=()=>{cancel();dialog.close();};
    dialog.addEventListener('close',cancel);
    dialog.addEventListener('cancel',cancel);
    document.addEventListener('visibilitychange',()=>{if(document.hidden)cancel();});
    new ResizeObserver(()=>{if(!playing)draw();}).observe($('drawCanvas'));
  }
  function setEnabled(enabled){
    ST.showHandwritingProcess=!!enabled;cancel();
    if(!enabled&&$('handwritingReviewDialog').open)$('handwritingReviewDialog').close();
    saveSettings();sync();
  }
  function sync(){
    if(!initialized)return;
    const enabled=ST.showHandwritingProcess;
    $('showHandwritingProcess').checked=enabled;
    $('btnProcessToggle').setAttribute('aria-pressed',String(enabled));
    $('btnProcessToggle').textContent='書いた順・向き '+(enabled?'ON':'OFF');
    $('btnStrokeReplay').hidden=$('btnInspectCharacter').hidden=!enabled;
    $('btnStrokeReplay').disabled=!ST.strokes.length||drawing;
    $('btnInspectCharacter').disabled=!characters[selected]||drawing;
    $('btnStrokeReplay').textContent=playing&&target==='word'?'■ 再生を とめる':'▶ かいた順に みる';
    $('btnCharacterReplay').textContent=playing&&target==='character'?'■ 再生を とめる':'▶ この字を 再生';
    draw();
  }
  function update(chars,index){
    init();
    if(playing||$('handwritingReviewDialog').open){
      // New ink, segmentation, or intended character invalidates the inspected snapshot.
      const old=characters[selected],next=chars[index];
      if(old?.segment!==next?.segment||old?.ch!==next?.ch||characters.length!==chars.length){
        cancel();if($('handwritingReviewDialog').open)$('handwritingReviewDialog').close();
      }
    }
    characters=chars;selected=index;sync();
  }
  function cancel(){
    cancelAnimationFrame(animation);animation=0;playing=false;target=null;
    if(initialized){$('strokeReviewStatus').textContent='';$('characterReviewStatus').textContent='';sync();}
  }
  function reset(){
    if(!initialized)return;
    cancel();if($('handwritingReviewDialog').open)$('handwritingReviewDialog').close();
    characters=[];selected=-1;
  }
  function ordered(strokes){
    const set=new Set(strokes);
    return ST.strokes.map((stroke,i)=>({stroke,number:i+1})).filter(row=>set.has(row.stroke));
  }
  function pathsForCharacter(){return characters[selected]?ordered(characters[selected].segment.strokes):[];}
  function mapping(character){
    if(character){
      const rows=pathsForCharacter();if(!rows.length)return null;
      const box=ShiritoriWordHandwriting.bounds(rows.map(r=>r.stroke));
      const scale=Math.min(270/box.w,200/box.h);
      return {rows:rows.map((row,i)=>({...row,localNumber:i+1})),width:340,height:280,point:p=>({x:(340-box.w*scale)/2+(p.x-box.l)*scale,y:(280-box.h*scale)/2+(p.y-box.t)*scale})};
    }
    const box=cv.getBoundingClientRect();
    const localNumbers=new Map();
    characters.forEach(c=>ordered(c.segment.strokes).forEach((row,i)=>localNumbers.set(row.stroke,i+1)));
    const single=ST.handwritingMode!=='word'||ST.charMode!=='hiragana';
    const rows=ordered(ST.strokes).map(row=>({...row,localNumber:localNumbers.get(row.stroke)??(single?row.number:null)}));
    return {rows,width:box.width,height:box.height,point:p=>({x:p.x*box.width/cv.width,y:p.y*box.height/cv.height})};
  }
  function strokePath(points){return points.map((p,i)=>(i?'L':'M')+p.x+','+p.y).join(' ');}
  function annotate(svg,rows,map,character=false,upto=rows.length,fraction=1){
    rows.slice(0,upto).forEach(({stroke,number,localNumber},index)=>{
      const points=stroke.points.map(map.point);if(!points.length)return;
      const partial=index===upto-1?fraction:1;
      const shown=prefix(points,partial),color=palette[((localNumber??1)-1)%palette.length];
      svg.appendChild(node('path',{d:strokePath(shown),stroke:color,'stroke-width':character?3:2.5,fill:'none','stroke-linecap':'round','stroke-linejoin':'round','data-stroke':number}));
      if(shown.length===1)svg.appendChild(node('circle',{cx:shown[0].x,cy:shown[0].y,r:2.5,fill:color}));
      if(partial<1)return;
      // Arrow near the middle uses the recorded path's tangent, including curved strokes.
      const at=Math.max(1,Math.floor(points.length*.6)),a=points[Math.max(0,at-1)],b=points[Math.min(points.length-1,at)];
      let dx=b.x-a.x,dy=b.y-a.y;
      if(Math.hypot(dx,dy)<.5){dx=points.at(-1).x-points[0].x;dy=points.at(-1).y-points[0].y;}
      if(Math.hypot(dx,dy)>.5){
        const angle=Math.atan2(dy,dx),size=8;
        const p=[{x:b.x-size*Math.cos(angle-.55),y:b.y-size*Math.sin(angle-.55)},b,{x:b.x-size*Math.cos(angle+.55),y:b.y-size*Math.sin(angle+.55)}];
        svg.appendChild(node('path',{d:strokePath(p),stroke:color,'stroke-width':2.5,fill:'none','class':'stroke-direction','data-stroke':number}));
      }
      const start=points[0];
      if(localNumber!=null){
        const label=String(localNumber),width=label.length*8+8,x=Math.max(2,Math.min(map.width-width-2,start.x+8)),y=Math.max(2,Math.min(map.height-21,start.y+5));
        svg.appendChild(node('rect',{x,y,width,height:20,rx:5,fill:'#fff',stroke:color}));
        svg.appendChild(node('text',{x:x+4,y:y+15,fill:color,'font-size':13,'font-weight':800,'class':'stroke-order','data-stroke':number},label));
      }
      svg.appendChild(node('circle',{cx:start.x,cy:start.y,r:3,fill:'#fff',stroke:color,'stroke-width':2}));
      if(points.length>1)svg.appendChild(node('circle',{cx:points.at(-1).x,cy:points.at(-1).y,r:1.8,fill:color,'class':'stroke-end'}));
    });
  }
  function prefix(points,fraction){
    if(fraction>=1)return points;if(points.length<2)return points;
    const lengths=[0];for(let i=1;i<points.length;i++)lengths.push(lengths.at(-1)+Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y));
    const distance=lengths.at(-1)*Math.max(0,fraction);let i=1;while(i<points.length&&lengths[i]<distance)i++;
    i=Math.min(i,points.length-1);const t=(distance-lengths[i-1])/(lengths[i]-lengths[i-1]||1);
    return [...points.slice(0,i),{x:points[i-1].x+(points[i].x-points[i-1].x)*t,y:points[i-1].y+(points[i].y-points[i-1].y)*t}];
  }
  function draw(){
    const svg=$('handwritingProcess');if(!svg)return;
    if(playing)return;
    svg.replaceChildren();
    if(!ST.showHandwritingProcess)return;
    const map=mapping(false);svg.setAttribute('viewBox',`0 0 ${map.width||1} ${map.height||1}`);
    annotate(svg,map.rows,map);
    if($('handwritingReviewDialog').open)drawCharacter();
  }
  function drawCharacter(){
    const map=mapping(true),svg=$('characterReviewSvg');svg.replaceChildren();
    if(map)annotate(svg,map.rows,map,true);
  }
  function openCharacter(){
    if(!ST.showHandwritingProcess||!characters[selected])return;
    cancel();$('handwritingReviewTitle').textContent=`${selected+1}もじめ「${characters[selected].ch}」の かきかた`;
    $('handwritingReviewDialog').showModal();drawCharacter();
  }
  function replay(character){
    if(!ST.showHandwritingProcess||drawing)return;
    cancel();const map=mapping(character);if(!map?.rows.length)return;
    const svg=$(character?'characterReviewSvg':'handwritingProcess');
    target=character?'character':'word';playing=true;sync();
    svg.setAttribute('viewBox',`0 0 ${map.width||1} ${map.height||1}`);
    const durations=map.rows.map(({stroke})=>{
      const points=stroke.points,elapsed=points.at(-1).t-points[0].t;
      return Number.isFinite(elapsed)?Math.max(250,Math.min(1200,elapsed)):550;
    });
    const start=performance.now();
    function frame(now){
      if(!playing)return;
      let elapsed=now-start,index=0;
      while(index<durations.length&&elapsed>durations[index]+140){elapsed-=durations[index]+140;index++;}
      if(index>=durations.length){cancel();return;}
      svg.replaceChildren();svg.appendChild(node('rect',{width:map.width,height:map.height,fill:'#fff','class':'replay-background'}));
      annotate(svg,map.rows,map,character,index+1,Math.min(1,elapsed/durations[index]));
      $(character?'characterReviewStatus':'strokeReviewStatus').textContent=character?`${index+1} / ${map.rows.length}画（この字で書いた順）`:'書いた順に 再生中…';
      animation=requestAnimationFrame(frame);
    }
    animation=requestAnimationFrame(frame);
  }
  return {update,cancel,reset,setEnabled};
})();
