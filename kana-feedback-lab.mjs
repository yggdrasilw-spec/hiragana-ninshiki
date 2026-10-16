import {HiraganaRecognizer,SMALL_KANA} from './kana-recognizer.mjs?v=20261017c';
import {evaluate,box,resample,SUPPORTED,ENGINE_VERSION} from './kana-feedback-engine.mjs?v=20261017c';
const $=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg',KEY='kana-feedback-review-v1';
let char=null,strokes=[],reference=[],drawing=null,result=null,source='じぶんで かいた じ',focus=null;
let data,candidates=[],busy=false,revision=0;
const recognizer=new HiraganaRecognizer();
const node=(tag,attrs={},text)=>{const n=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,v);if(text!=null)n.textContent=text;return n;};
const path=points=>points.map((p,i)=>(i?'L':'M')+p.x+','+p.y).join(' ');
function frame(rows){const b=box(rows),scale=230/Math.max(b.w,b.h);return rows.map((s,i)=>({id:'reference-'+i,points:s.points.map(p=>({x:160+(p.x-(b.l+b.r)/2)*scale,y:160+(p.y-(b.t+b.b)/2)*scale}))}));}
function sampleReference(ch){
  return frame(data.glyphs[ch].paths.map((d,i)=>{const p=node('path',{d}),length=p.getTotalLength();return {id:'ref-'+i,points:Array.from({length:64},(_,j)=>{const q=p.getPointAtLength(length*j/63);return {x:q.x,y:q.y};})};}));
}
function marks(parent,rows){
  if(!$('showDirections').checked)return;
  rows.forEach((s,i)=>{
    const points=resample(s.points,32),a=points[18],b=points[20],angle=Math.atan2(b.y-a.y,b.x-a.x),start=s.points[0];
    if(Math.hypot(b.x-a.x,b.y-a.y)>.1){const tip=[{x:b.x-8*Math.cos(angle-.55),y:b.y-8*Math.sin(angle-.55)},b,{x:b.x-8*Math.cos(angle+.55),y:b.y-8*Math.sin(angle+.55)}];parent.append(node('path',{d:path(tip),fill:'none',stroke:'#1765cd','stroke-width':2.5,class:'direction-mark'}));}
    parent.append(node('circle',{cx:start.x,cy:start.y,r:3,fill:'#fff',stroke:'#1765cd','stroke-width':2}));
    parent.append(node('text',{x:Math.min(300,start.x+7),y:Math.min(308,start.y+17),fill:'#1765cd','font-size':14,class:'order-mark'},i+1));
  });
}
function renderInk(){
  $('ink').replaceChildren();$('focus').replaceChildren();
  strokes.forEach((s,i)=>{
    $('ink').append(node('path',{d:path(s.points),class:'ink-path'+(focus?.strokeIndices.includes(i)?' highlight':''),'data-stroke':i+1}));
    if(s.points.length===1)$('ink').append(node('circle',{cx:s.points[0].x,cy:s.points[0].y,r:2.5,fill:'#233348'}));
  });
  if(focus?.point)$('focus').append(node('circle',{cx:focus.point.x,cy:focus.point.y,r:13,fill:'none',stroke:'#e78816','stroke-width':3}));
  $('reference').replaceChildren();$('ghost').replaceChildren();
  reference.forEach((s,i)=>{
    $('reference').append(node('path',{d:path(s.points),class:'reference-path'+(focus?.referenceIndices.includes(i)?' highlight':'')}));
    if($('showGhost').checked)$('ghost').append(node('path',{d:path(s.points),class:'reference-path'}));
  });
  marks($('ink'),strokes);marks($('reference'),reference);
  $('read').disabled=!strokes.length||!!drawing||busy;$('compare').hidden=!char;
  $('inkSource').textContent=source;$('compare').disabled=!strokes.length||!!drawing;$('undo').disabled=!strokes.length||!!drawing;
}
function resetResult(){result=null;focus=null;$('caseKind').value='uncertain';$('adviceRating').value='unreviewed';$('advice').replaceChildren();$('message').textContent='まる・ばつは つけないよ。かいた じを たしかめよう。';$('measurements').textContent='まだ比較していません。';}
function forget(){revision++;busy=false;char=null;reference=[];candidates=[];$('referenceChar').textContent='';$('referenceHint').textContent='よみとると、ここに おてほんが でるよ。';$('recognitionCandidates').replaceChildren();$('otherCharacters').hidden=true;$('recognitionMessage').textContent='１もじ かいて、「よみとる」を おしてね。';resetResult();}
function select(ch){if(!data.glyphs[ch])return;revision++;busy=false;char=ch;reference=sampleReference(ch);resetResult();$('referenceChar').textContent=ch;$('referenceHint').textContent='いろの せんどうしを くらべてね。';document.querySelectorAll('[data-character]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.character===ch)));if(strokes.length)compare();renderInk();}
async function prepare(){ $('retryModel').hidden=true;try{await recognizer.load();$('modelStatus').textContent='よみとる じゅんびが できたよ。';}catch{$('modelStatus').textContent='じゅんびが できなかったよ。もういちど ためしてね。';$('retryModel').hidden=false;}}
async function read(){if(!strokes.length||drawing||busy)return;forget();const token=revision,snapshot=structuredClone(strokes);busy=true;renderInk();$('recognitionMessage').textContent='よみとって いるよ。';try{const found=await recognizer.recognize(snapshot);if(token!==revision)return;candidates=found;$('recognitionCandidates').replaceChildren();const choices=[...found.map(r=>r.ch),...found.map(r=>SMALL_KANA[r.ch]).filter(Boolean)];for(const ch of new Set(choices)){const b=document.createElement('button');b.textContent=ch;b.dataset.candidate=ch;b.onclick=()=>select(ch);$('recognitionCandidates').append(b);}$('recognitionMessage').textContent=choices.length?'かいた じを おして、おてほんと くらべよう。':'もうすこし おおきく かいてみよう。';$('otherCharacters').hidden=false;}catch{if(token!==revision)return;$('recognitionMessage').textContent='よみとれなかったよ。もういちど かくか、じを えらんでね。';$('otherCharacters').hidden=false;$('retryModel').hidden=false;}finally{if(token===revision){busy=false;renderInk();}}}
$('read').onclick=read;$('retryModel').onclick=prepare;
function compare(){
  if(drawing||!char||!strokes.length)return;
  result=evaluate({char,strokes,reference});focus=null;$('message').textContent=result.message;$('advice').replaceChildren();
  const rows=[...result.writing,...result.beauty];
  rows.forEach((item,i)=>{
    const card=document.createElement('article');card.className='advice-card';card.dataset.rule=item.id;
    const layer=document.createElement('span');layer.className='layer';layer.textContent=item.layer==='beauty'?'じの かたちの ヒント':'かきかたの ヒント';
    const h=document.createElement('h3');h.textContent=item.title;const p=document.createElement('p');p.textContent=item.text;
    const b=document.createElement('button');b.type='button';b.textContent='ここを みる';b.setAttribute('aria-pressed','false');
    b.onclick=()=>{focus=item.focus;document.querySelectorAll('.advice-card button').forEach(n=>n.setAttribute('aria-pressed',String(n===b)));renderInk();$('writing').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'center'});};card.append(layer,h,p,b);$('advice').append(card);
    if(i===0){focus=item.focus;b.setAttribute('aria-pressed','true');}
  });
  $('measurements').textContent=JSON.stringify({engineVersion:ENGINE_VERSION,identity:result.identity,metrics:result.metrics,mapping:result.mapping,observations:rows.map(({focus,...rest})=>rest)},null,2);renderInk();
}
function demo(kind){
  drawing=null;select($('demoCharacter').value||char||'し');resetResult();source='検証用の作図例';
  strokes=structuredClone(reference).map((s,i)=>({...s,id:'demo-'+i}));
  if(kind==='wide')strokes.forEach(s=>s.points=s.points.map(p=>({x:160+(p.x-160)*1.35,y:160+(p.y-160)*.75})));
  if(kind==='reverse')strokes.forEach(s=>s.points.reverse());
  if(kind==='short'){if(strokes.length>1)strokes.pop();else strokes[0].points=strokes[0].points.slice(0,32);}
  renderInk();compare();
}
function point(event){const m=$('writing').getScreenCTM().inverse(),p=new DOMPoint(event.clientX,event.clientY).matrixTransform(m);return {x:Math.max(4,Math.min(316,p.x)),y:Math.max(4,Math.min(316,p.y)),t:performance.now()};}
$('writing').addEventListener('pointerdown',e=>{
  if(drawing||e.button!==0)return;e.preventDefault();
  if(source==='検証用の作図例')strokes=[];
  source='じぶんで かいた じ';forget();drawing={pointerId:e.pointerId};$('writing').setPointerCapture(e.pointerId);
  strokes.push({id:'ink-'+performance.now(),points:[point(e)]});renderInk();
});
$('writing').addEventListener('pointermove',e=>{if(drawing?.pointerId!==e.pointerId)return;e.preventDefault();const p=point(e),last=strokes.at(-1).points.at(-1);if(Math.hypot(p.x-last.x,p.y-last.y)>.5)strokes.at(-1).points.push(p);renderInk();});
for(const name of ['pointerup','pointercancel','lostpointercapture'])$('writing').addEventListener(name,e=>{if(drawing?.pointerId!==e.pointerId)return;drawing=null;renderInk();});
$('compare').onclick=()=>{compare();$('resultTitle').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});};$('clear').onclick=()=>{strokes=[];drawing=null;source='じぶんで かいた じ';forget();renderInk();};
$('undo').onclick=()=>{strokes.pop();forget();renderInk();};$('showGhost').onchange=renderInk;$('showDirections').onchange=renderInk;
document.querySelectorAll('[data-demo]').forEach(b=>b.onclick=()=>demo(b.dataset.demo));
function saved(){try{const a=JSON.parse(localStorage.getItem(KEY)||'[]');return Array.isArray(a)?a:[];}catch{return [];}}
$('saveCase').onclick=()=>{
  if(!char||!strokes.length||drawing){$('savedStatus').textContent='筆跡を読み取り、文字を選んでから保存してください。';return;}
  if(!result)compare();
  const record={version:2,char,candidates,strokes:structuredClone(strokes),source,caseKind:$('caseKind').value,adviceRating:$('adviceRating').value,note:$('reviewNote').value,expected:reference,evaluation:result,referenceSource:{author:data.author,url:data.url,license:data.license,licenseUrl:data.licenseUrl,inputSha256:data.inputSha256},savedAt:new Date().toISOString()};
  try{const records=[...saved(),record].slice(-100);localStorage.setItem(KEY,JSON.stringify(records));$('savedStatus').textContent=`${records.length}例を端末に保存しました。`;}catch{$('savedStatus').textContent='保存できませんでした。端末の空き容量を確認してください。';}
};
$('exportCases').onclick=()=>{
  const records=saved();if(!records.length){$('savedStatus').textContent='先に比較した例を保存してください。';return;}
  const url=URL.createObjectURL(new Blob([JSON.stringify({version:1,engineVersion:ENGINE_VERSION,referenceLicense:data.license,records},null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='kana-feedback-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
};
try{
  const response=await fetch('./data/kana-feedback-reference.json');if(!response.ok)throw Error('reference');data=await response.json();
  for(const ch of SUPPORTED){const b=document.createElement('button');b.type='button';b.dataset.character=ch;b.textContent=ch;b.onclick=()=>select(ch);$('characters').append(b);const option=document.createElement('option');option.value=ch;option.textContent=ch;$('demoCharacter').append(option);}
  const query=new URLSearchParams(location.search),initial=query.get('char');$('demoCharacter').value=SUPPORTED.includes(initial)?initial:'し';renderInk();prepare();
  if(['reference','wide','reverse','short'].includes(query.get('demo')))demo(query.get('demo'));
}catch{$('message').textContent='お手本を読み込めませんでした。HTTPサーバーから開いてください。';}
window.KanaFeedbackLab={select,demo,compare,read,getState:()=>({ready:!!data,char,strokes,reference,result,candidates,busy}),setStrokes:rows=>{forget();strokes=structuredClone(rows);source='じぶんで かいた じ';drawing=null;renderInk();}};
