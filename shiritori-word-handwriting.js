/* Left-to-right kana segmentation. No vocabulary/game-state correction. */
(function(root){
  'use strict';
  const smallMap={あ:'ぁ',い:'ぃ',う:'ぅ',え:'ぇ',お:'ぉ',や:'ゃ',ゆ:'ゅ',よ:'ょ',つ:'っ',わ:'ゎ'};
  for(const [large,small] of Object.entries(smallMap)){
    smallMap[String.fromCharCode(large.charCodeAt(0)+0x60)]=String.fromCharCode(small.charCodeAt(0)+0x60);
  }
  const largeMap=Object.fromEntries(Object.entries(smallMap).map(([a,b])=>[b,a]));
  function bounds(strokes){
    const points=strokes.flatMap(s=>s.points);
    const xs=points.map(p=>p.x),ys=points.map(p=>p.y);
    const l=Math.min(...xs),r=Math.max(...xs),t=Math.min(...ys),b=Math.max(...ys);
    return {l,r,t,b,w:Math.max(1,r-l),h:Math.max(1,b-t)};
  }
  function plan(strokes){
    if(!strokes.length)return {segments:[],count:0};
    if(strokes.length>64||strokes.reduce((n,s)=>n+s.points.length,0)>24000)throw Error('too-many-strokes');
    const sorted=strokes.map((s,index)=>({s,index,box:bounds([s])})).sort((a,b)=>(a.box.l+a.box.r)-(b.box.l+b.box.r));
    const whole=bounds(strokes),height=Math.max(12,whole.h);
    const segments=[];
    for(let start=0;start<sorted.length;start++){
      for(let end=start+1;end<=Math.min(sorted.length,start+10);end++){
        const members=sorted.slice(start,end),box=bounds(members.map(m=>m.s));
        if(box.w>height*1.65&&end>start+1)continue;
        // Wide spaces inside a proposed character are evidence against merging.
        let gap=0,right=members[0].box.r;
        for(const m of members.slice(1)){gap=Math.max(gap,m.box.l-right);right=Math.max(right,m.box.r);}
        const next=sorted[end],overlap=next?Math.max(0,box.r-next.box.l):0;
        const cutCost=next?Math.max(0,.26-(next.box.l-box.r)/height)*4:0;
        const geometry=Math.max(0,box.w/height-1.12)*4+Math.max(0,gap/height-.20)*4+
          Math.max(0,.32-box.h/height)*7+Math.min(2,overlap/height*3)+cutCost;
        segments.push({start,end,box,geometry,nextBox:next?.box,indices:members.map(m=>m.index),strokes:members.map(m=>m.s)});
      }
    }
    return {segments,count:sorted.length,height,whole};
  }
  function alternatives(segment,predictions,plan){
    const result=[];
    const ratio=segment.box.h/plan.height;
    // Size is only evidence, never a forced conversion. All-small writing stays large.
    const compact=ratio<.73&&segment.box.w/plan.height<.8;
    // A very thin し next to more tall ink may be the left stroke of け / は.
    // Keep the standalone candidate, but let the joint character compete fairly.
    const b=segment.box,next=segment.nextBox;
    const thinShi=b.w/b.h<.22&&ratio>.45&&next&&next.h>plan.height*.45&&
      next.l-b.r<plan.height*.38&&Math.min(b.b,next.b)-Math.max(b.t,next.t)>plan.height*.35;
    for(const p of predictions.slice(0,4)){
      const base=largeMap[p.ch]||p.ch;
      const options=smallMap[base]?[base,smallMap[base]]:[base];
      for(const ch of options){
        const small=ch!==base;
        const sizeCost=small?(compact ? .10 : 1.6):(compact&&smallMap[base] ? .42 : 0);
        const fragmentCost=base==='し'&&thinShi?2.4:0;
        result.push({ch,score:Math.log(Math.max(p.p,1e-7))+.3-sizeCost-fragmentCost-segment.geometry,segment});
      }
    }
    if(segment.box.w>plan.height*.25&&segment.box.h<plan.height*.14){
      result.push({ch:'ー',score:.1-segment.geometry,segment});
    }
    return result.sort((a,b)=>b.score-a.score);
  }
  function detachedMarkCost(previous,choice,height){
    if(!previous||!['い','ぃ','ー'].includes(choice.ch))return 0;
    if(!/^[かきくけこさしすせそたちつてとはひふへほう]$/.test(previous.ch))return 0;
    const mark=choice.segment,body=previous.segment.box,b=mark.box;
    // Short strokes at the preceding hiragana's upper right resemble ゛, even
    // if a split leaves just one of the two marks (or suggests a horizontal ー).
    // Compare with the local body as well as line height; a normal next い stays intact.
    const smallPair=mark.strokes.length>=1&&mark.strokes.length<=2&&b.w<height*.48&&b.h<height*.32&&
      mark.strokes.every(s=>{const box=bounds([s]);return Math.max(box.w,box.h)<height*.32;});
    const upperRight=body.h>height*.55&&b.l>=body.l+body.w*.55&&
      b.l-body.r<height*.35&&b.t>=body.t-height*.2&&b.b<body.t+body.h*.42;
    return smallPair&&upperRight?3.2:0;
  }
  function decode(plan,predictions,{isKnown}={}){
    if(!plan.count)return [];
    const beams=Array.from({length:plan.count+1},()=>[]);beams[0]=[{text:'',score:0,chars:[]}];
    const byStart=Array.from({length:plan.count},()=>[]);
    plan.segments.forEach((s,i)=>byStart[s.start].push({s,i}));
    for(let at=0;at<plan.count;at++){
      beams[at].sort((a,b)=>b.score-a.score);beams[at]=beams[at].slice(0,8);
      for(const {s,i} of byStart[at]){
        const choices=alternatives(s,predictions[i]||[],plan);
        for(const prev of beams[at])for(const c of choices.slice(0,4)){
          if(prev.chars.length>=16)continue;
          const markCost=detachedMarkCost(prev.chars[prev.chars.length-1],c,plan.height);
          beams[s.end].push({text:prev.text+c.ch,score:prev.score+c.score-markCost,chars:[...prev.chars,{ch:c.ch,segment:s,choices}]});
        }
        // Bound memory even for dense overlapping strokes.
        if(beams[s.end].length>160)beams[s.end]=beams[s.end].sort((a,b)=>b.score-a.score).slice(0,40);
      }
    }
    const unique=new Map();
    for(const b of beams[plan.count].sort((a,b)=>b.score-a.score))if(!unique.has(b.text))unique.set(b.text,b);
    return rankCandidates([...unique.values()],isKnown);
  }
  function rankCandidates(candidates,isKnown=()=>false,limit=5){
    // Dictionary membership changes order only; keep the model's text and stroke ranges.
    return candidates.map(candidate=>({candidate,known:!!isKnown(candidate.text)}))
      .sort((a,b)=>Number(b.known)-Number(a.known)||b.candidate.score-a.candidate.score)
      .slice(0,limit).map(item=>item.candidate);
  }
  const api={bounds,plan,decode,rankCandidates,alternatives,smallMap,largeMap};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.ShiritoriWordHandwriting=api;
})(typeof globalThis!=='undefined'?globalThis:this);
