// Same 71-class hiragana model as shiritori; recognition is separate from shape feedback.
// Keep the exact training label order (small kana are selected after recognition).
export const MODEL_LABELS=['あ','い','う','え','お','か','が','き','ぎ','く','ぐ','け','げ','こ','ご','さ','ざ','し','じ','す','ず','せ','ぜ','そ','ぞ','た','だ','ち','ぢ','つ','づ','て','で','と','ど','な','に','ぬ','ね','の','は','ば','ぱ','ひ','び','ぴ','ふ','ぶ','ぷ','へ','べ','ぺ','ほ','ぼ','ぽ','ま','み','む','め','も','や','ゆ','よ','ら','り','る','れ','ろ','わ','を','ん'];
export const SMALL_KANA={あ:'ぁ',い:'ぃ',う:'ぅ',え:'ぇ',お:'ぉ',や:'ゃ',ゆ:'ゅ',よ:'ょ',つ:'っ',わ:'ゎ',か:'ゕ',け:'ゖ'};
let runtimePromise;
async function runtime(){
  if(globalThis.tf)return globalThis.tf;
  if(!runtimePromise)runtimePromise=new Promise((resolve,reject)=>{
    const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js';script.async=true;
    script.onload=()=>globalThis.tf?resolve(globalThis.tf):reject(Error('runtime'));
    script.onerror=()=>{script.remove();reject(Error('runtime'));};document.head.appendChild(script);
  }).catch(error=>{runtimePromise=null;throw error;});
  return runtimePromise;
}
export function rasterize(strokes){
  const points=strokes.flatMap(s=>s.points);
  if(!points.length||points.length>12000||strokes.length>12||points.some(p=>!Number.isFinite(p.x)||!Number.isFinite(p.y)))return null;
  const xs=points.map(p=>p.x),ys=points.map(p=>p.y),l=Math.min(...xs),r=Math.max(...xs),t=Math.min(...ys),b=Math.max(...ys),size=Math.max(r-l,b-t);
  if(size<4)return null;
  let total=0;for(const s of strokes)for(let i=1;i<s.points.length;i++)total+=Math.hypot(s.points[i].x-s.points[i-1].x,s.points[i].y-s.points[i-1].y);
  if(total<8)return null;
  const canvas=document.createElement('canvas');canvas.width=canvas.height=64;
  const ctx=canvas.getContext('2d',{willReadFrequently:true}),scale=52/size;
  ctx.fillStyle='#000';ctx.fillRect(0,0,64,64);ctx.strokeStyle=ctx.fillStyle='#fff';ctx.lineWidth=3;ctx.lineCap=ctx.lineJoin='round';
  for(const stroke of strokes){
    const pts=stroke.points.map(p=>({x:32+(p.x-(l+r)/2)*scale,y:32+(p.y-(t+b)/2)*scale}));
    ctx.beginPath();ctx.arc(pts[0].x,pts[0].y,1.5,0,Math.PI*2);ctx.fill();
    ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);for(const p of pts.slice(1))ctx.lineTo(p.x,p.y);ctx.stroke();
  }
  const pixels=ctx.getImageData(0,0,64,64).data;return Float32Array.from({length:4096},(_,i)=>pixels[i*4]/255);
}
export class HiraganaRecognizer{
  constructor(){this.model=null;this.pending=null;this.tf=null;}
  async load(){
    if(this.model)return;
    if(!this.pending)this.pending=(async()=>{
      this.tf=await runtime();const model=await this.tf.loadLayersModel(new URL('./tfjs_model/hiragana/model.json',import.meta.url).href);
      let input,output;
      try{input=this.tf.zeros([1,64,64,1]);output=model.predict(input);const values=await output.data();if(values.length!==MODEL_LABELS.length)throw Error('labels');}
      catch(error){model.dispose();throw error;}
      finally{input?.dispose();output?.dispose();}
      this.model=model;
    })().catch(error=>{this.pending=null;throw error;});
    return this.pending;
  }
  async recognize(strokes){
    const data=rasterize(strokes);if(!data)return [];
    await this.load();let input,output;
    try{
      input=this.tf.tensor4d(data,[1,64,64,1]);output=this.model.predict(input);const values=await output.data();
      if(values.length!==MODEL_LABELS.length||Array.from(values).some(p=>!Number.isFinite(p)))throw Error('output');
      return MODEL_LABELS.map((ch,i)=>({ch,probability:values[i]})).sort((a,b)=>b.probability-a.probability).slice(0,5);
    }finally{input?.dispose();output?.dispose();}
  }
}
