/* Shared inference contract for the game and the handwriting laboratory. */
(() => {
  'use strict';
  const hira = [...'あいうえおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゆよらりるれろわをん'];
  const kata = [...'ヲアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン'];
  const marks = [...kata,...'ガギグゲゴザジズゼゾダヂヅデドバビブベボヴパピプペポ'];
  const models = [
    {id:'hiragana',script:'hiragana',name:'ひらがな・既存71文字',format:'layers',labels:hira,url:'./tfjs_model/hiragana/model.json'},
    {id:'katakana',script:'katakana',name:'カタカナ・既存46文字',format:'graph',labels:kata,url:'./tfjs_model/katakana/model.json'},
    {id:'katakana-marks-20261018',script:'katakana',name:'カタカナ・濁点半濁点72文字（試用）',format:'graph',labels:marks,url:'./tfjs_model/katakana-marks-20261018/model.json'}
  ];
  function preprocess(source) {
    const mid=document.createElement('canvas');
    mid.width=Math.round(source.getBoundingClientRect?.().width)||source.width;
    mid.height=Math.round(source.getBoundingClientRect?.().height)||source.height;
    const ctx=mid.getContext('2d',{willReadFrequently:true});
    ctx.fillStyle='#fff';ctx.fillRect(0,0,mid.width,mid.height);ctx.drawImage(source,0,0,mid.width,mid.height);
    const {data}=ctx.getImageData(0,0,mid.width,mid.height);
    let l=mid.width,r=-1,t=mid.height,b=-1;
    for(let y=0;y<mid.height;y++)for(let x=0;x<mid.width;x++){
      const i=(y*mid.width+x)*4;
      if((data[i]+data[i+1]+data[i+2])/3<245){l=Math.min(l,x);r=Math.max(r,x);t=Math.min(t,y);b=Math.max(b,y);}
    }
    if(r<l)return null;
    const w=r-l+1,h=b-t+1,cut=document.createElement('canvas');cut.width=w;cut.height=h;
    const cc=cut.getContext('2d'),image=ctx.getImageData(l,t,w,h);
    for(let i=0;i<image.data.length;i+=4){image.data[i]=255-image.data[i];image.data[i+1]=255-image.data[i+1];image.data[i+2]=255-image.data[i+2];image.data[i+3]=255;}
    cc.putImageData(image,0,0);
    const out=document.createElement('canvas');out.width=out.height=64;
    const oc=out.getContext('2d',{willReadFrequently:true});oc.fillStyle='#000';oc.fillRect(0,0,64,64);
    const scale=Math.min(64/w,64/h)*.85,dw=Math.max(1,Math.round(w*scale)),dh=Math.max(1,Math.round(h*scale));
    oc.imageSmoothingEnabled=true;oc.imageSmoothingQuality='high';oc.drawImage(cut,Math.floor((64-dw)/2),Math.floor((64-dh)/2),dw,dh);
    const pixels=oc.getImageData(0,0,64,64).data;
    return Float32Array.from({length:4096},(_,i)=>pixels[i*4]/255);
  }
  async function predict(model, labels, pixels) {
    const input=tf.tensor4d(pixels,[1,64,64,1]);let output;
    try{output=model.predict(input);const values=await output.data();if(values.length!==labels.length||!values.every(Number.isFinite))throw Error('モデルの出力と文字一覧が一致しません');return labels.map((label,i)=>({label,score:values[i]})).sort((a,b)=>b.score-a.score);}
    finally{input.dispose();output?.dispose();}
  }
  async function load(spec) {
    const model=await(spec.format==='graph'?tf.loadGraphModel(spec.url):tf.loadLayersModel(spec.url));
    try{await predict(model,spec.labels,new Float32Array(4096));return model;}catch(e){model.dispose();throw e;}
  }
  async function loadFiles(files,script) {
    const list=Array.from(files),modelFile=list.find(f=>f.name==='model.json'),labelsFile=list.find(f=>f.name==='labels.json');
    if(!modelFile||!labelsFile)throw Error('model.json と labels.json を一緒に選んでください');
    const json=JSON.parse(await modelFile.text()),labels=JSON.parse(await labelsFile.text()),allowed=script==='hiragana'?hira:marks;
    if(!Array.isArray(labels)||!labels.length||new Set(labels).size!==labels.length||labels.some(c=>!allowed.includes(c)))throw Error('文字の種類とlabels.jsonが一致しません');
    const prepFile=list.find(f=>f.name==='preprocessing.json');
    if(prepFile){const p=JSON.parse(await prepFile.text());if(p.size!==64||p.channels!==1||p.bbox_fit!==.85||p.ink!=='white'||p.background!=='black')throw Error('未対応の前処理です');}
    const io=tf.io.browserFiles([modelFile,...list.filter(f=>f.name.endsWith('.bin'))]);
    const model=await(json.format==='graph-model'?tf.loadGraphModel(io):tf.loadLayersModel(io));
    try{await predict(model,labels,new Float32Array(4096));return{model,labels};}catch(e){model.dispose();throw e;}
  }
  // These three bundled models share the verified CNN architecture. Reconstruct a
  // separate LayersModel from their weights; the source GraphModel stays intact.
  async function trainable(spec) {
    const response=await fetch(spec.url);if(!response.ok)throw Error('モデルを取得できません');const json=await response.json();
    const weights=await tf.io.loadWeights(json.weightsManifest,new URL('.',new URL(spec.url,location.href)).href);
    const model=tf.sequential();
    for(let i=0;i<3;i++){
      model.add(tf.layers.conv2d({...(i===0?{inputShape:[64,64,1]}:{}),filters:32,kernelSize:3,activation:'relu'}));
      model.add(tf.layers.maxPooling2d({poolSize:[2,2]}));model.add(tf.layers.dropout({rate:.25}));
    }
    model.add(tf.layers.flatten());model.add(tf.layers.dense({units:512,activation:'relu'}));model.add(tf.layers.dropout({rate:.25}));model.add(tf.layers.dense({units:spec.labels.length,activation:'softmax'}));
    const ordered=Object.values(weights).filter(w=>w.rank>=1 && !(w.dtype==='int32'));
    try{
      if(ordered.length!==10)throw Error('追加学習に未対応のモデル構造です');
      model.setWeights(ordered);
      // Tune only the classification head, retaining feature extraction.
      model.layers.forEach((layer,i)=>layer.trainable=i===model.layers.length-1);
      model.compile({optimizer:tf.train.adam(.0001),loss:'categoricalCrossentropy',metrics:['accuracy']});return model;
    }catch(e){model.dispose();throw e;}finally{Object.values(weights).forEach(w=>w.dispose());}
  }
  window.KanaModels={models,preprocess,predict,load,loadFiles,trainable};
})();
