// Uncalibrated comparison observations. No automatic pass/fail or mastery score.
export const ENGINE_VERSION='kana-observation-2';
export const SUPPORTED=Array.from({length:86},(_,i)=>String.fromCharCode(0x3041+i));
export function box(strokes){
  const pts=strokes.flatMap(s=>s.points),xs=pts.map(p=>p.x),ys=pts.map(p=>p.y);
  if(!pts.length)return null;
  const l=Math.min(...xs),r=Math.max(...xs),t=Math.min(...ys),b=Math.max(...ys);
  return {l,r,t,b,w:Math.max(1e-6,r-l),h:Math.max(1e-6,b-t)};
}
export function length(points){return points.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p.x-points[i].x,p.y-points[i].y),0);}
export function resample(points,count=48){
  if(!points.length)return [];
  const distances=[0];for(let i=1;i<points.length;i++)distances.push(distances.at(-1)+Math.hypot(points[i].x-points[i-1].x,points[i].y-points[i-1].y));
  const total=distances.at(-1);let cursor=1;
  return Array.from({length:count},(_,i)=>{
    if(!total)return {...points[0]};
    const target=i*total/(count-1);while(cursor<points.length-1&&distances[cursor]<target)cursor++;
    const a=points[cursor-1],b=points[cursor],f=(target-distances[cursor-1])/(distances[cursor]-distances[cursor-1]||1);
    return {x:a.x+(b.x-a.x)*f,y:a.y+(b.y-a.y)*f};
  });
}
function normalize(strokes){
  const b=box(strokes),size=Math.max(b.w,b.h);
  return strokes.map(s=>({...s,points:resample(s.points).map(p=>({x:(p.x-(b.l+b.r)/2)/size,y:(p.y-(b.t+b.b)/2)/size}))}));
}
const distance=(a,b)=>a.reduce((sum,p,i)=>sum+Math.hypot(p.x-b[i].x,p.y-b[i].y),0)/a.length;
export function match(actual,reference){
  if(!Array.isArray(actual)||!Array.isArray(reference)||!actual.length||!reference.length)return {available:false,reason:'input'};
  if(actual.length!==reference.length||actual.length>8)return {available:false,reason:'count'};
  const a=normalize(actual),r=normalize(reference),count=a.length;
  const matrix=r.map((ref,j)=>a.map((row,index)=>{
      const forward=distance(row.points,ref.points),reverse=distance([...row.points].reverse(),ref.points);
      return {index,reference:j,cost:Math.min(forward,reverse),reversed:reverse+.015<forward,directionClear:Math.abs(forward-reverse)>.04};
  }));
  // Retain the two best assignments per subset, avoiding factorial growth for voiced kana.
  const states=Array.from({length:1<<count},()=>[]);states[0]=[{pairs:[],cost:0}];
  for(let mask=0;mask<states.length;mask++){
    for(const state of states[mask])for(let index=0;index<count;index++){
      if(mask&(1<<index))continue;
      const pair=matrix[state.pairs.length][index],next=mask|(1<<index);
      states[next].push({pairs:[...state.pairs,pair],cost:state.cost+pair.cost/count});
      states[next].sort((a,b)=>a.cost-b.cost);states[next]=states[next].slice(0,2);
    }
  }
  const scores=states.at(-1),best=scores[0];
  return {...best,available:best.cost<.18&&(!scores[1]||scores[1].cost-best.cost>.025),reason:best.cost>=.18?'shape':'ambiguous'};
}
function curvature(points){
  const pts=resample(points),samples=[];
  for(let i=3;i<pts.length-3;i++){
    const a=pts[i-3],b=pts[i],c=pts[i+3],u={x:b.x-a.x,y:b.y-a.y},v={x:c.x-b.x,y:c.y-b.y};
    const angle=Math.abs(Math.atan2(u.x*v.y-u.y*v.x,u.x*v.x+u.y*v.y));samples.push({angle,index:i});
  }
  return samples.sort((a,b)=>b.angle-a.angle)[0]||{angle:0,index:0};
}
export function evaluate({char,strokes,reference}){
  const result={engineVersion:ENGINE_VERSION,char,identity:{status:'unavailable',reason:'字形の正誤は未判定。規則は人手レビュー・実筆跡での校正前です。'},writing:[],beauty:[],metrics:{},mapping:{available:false},reviewStatus:'uncalibrated'};
  const valid=rows=>Array.isArray(rows)&&rows.length>0&&rows.length<=12&&rows.reduce((n,s)=>n+(s.points?.length||0),0)<=12000&&rows.every(s=>Array.isArray(s.points)&&s.points.length&&s.points.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)));
  if(!SUPPORTED.includes(char)){result.message='この じの おてほんは、まだ ないよ。';return result;}
  if(!valid(strokes)||!valid(reference)){result.message='じを かいて、「よみとる」を おしてね。';return result;}
  const bounds=box(strokes),refBox=box(reference);
  if(Math.max(bounds.w,bounds.h)<4||strokes.some(s=>length(s.points)<2)){
    result.message='もうすこし おおきく じを かいてみよう。';return result;
  }
  result.metrics={strokes:strokes.length,referenceStrokes:reference.length,aspect:bounds.w/bounds.h,referenceAspect:refBox.w/refBox.h};
  result.mapping=match(strokes,reference);
  if(!result.mapping.available){result.message='おてほんと ならべて、せんを ひとつずつ たしかめてみよう。';return result;}
  const add=(list,id,title,text,indices,referenceIndices,observed,expected,point=null)=>list.push({id,layer:list===result.beauty?'beauty':'writing',status:'candidate',title,text,focus:{strokeIndices:indices,referenceIndices,point},observed,expected,reviewStatus:'unreviewed',thresholdSource:'prototype-only'});
  const aspect=result.metrics.aspect/result.metrics.referenceAspect;
  if(aspect>1.28||aspect<.78)add(result.beauty,'outline','じの かたち',aspect>1.28?'もうすこし たてに ながく かいてみよう。':'もうすこし よこに ひろげて かいてみよう。',strokes.map((_,i)=>i),reference.map((_,i)=>i),result.metrics.aspect,result.metrics.referenceAspect);
  const pairs=result.mapping.pairs;
  const actualLengths=strokes.map(s=>length(s.points)),refLengths=reference.map(s=>length(s.points));
  pairs.forEach((pair,j)=>{
    const index=pair.index,stroke=strokes[index],ref=reference[j];
    if(pair.cost>.20)return;
    if(index!==j)add(result.writing,'order-'+j,'かく じゅんばん',`いろの せんを、${j+1}ばんめに かいてみよう。`,[index],[j],index+1,j+1);
    if(pair.reversed&&pair.directionClear)add(result.writing,'direction-'+j,'かく むき','いろの せんは、おてほんの やじるしの むきに かいてみよう。',[index],[j],'お手本と逆向きの候補','お手本の矢印');
    if(pairs.length>1){
      const a=actualLengths[index]/Math.max(...actualLengths),r=refLengths[j]/Math.max(...refLengths);
      if(Math.abs(a-r)>.18)add(result.beauty,'length-'+j,'せんの ながさ',a>r?'いろの せんを、もうすこし みじかく かいてみよう。':'いろの せんを、もうすこし ながく かいてみよう。',[index],[j],a,r);
    }
    if(['し','つ'].includes(char)){
      const a=curvature(stroke.points),r=curvature(ref.points);
      if(a.angle>r.angle+.65&&a.angle>.85)add(result.beauty,'curve-'+j,'まがる ところ','いろの ところを、もうすこし まるく まげてみよう。',[index],[j],a.angle,r.angle,resample(stroke.points)[a.index]);
    }
  });
  result.message=result.writing.length||result.beauty.length?'いろの ついた ところを、おてほんと くらべてみよう。':'おてほんと くらべて、じの かたちを たしかめよう。';
  return result;
}
