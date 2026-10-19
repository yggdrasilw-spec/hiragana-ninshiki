// Public objects are downloaded through the actual read-only delivery Worker.
// Private source sheets are checked against the R2 single-PUT ETag (MD5).
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/image-coverage/2026-10-19-nature512');
const entries=JSON.parse(fs.readFileSync(path.join(dir,'r2-upload.json'),'utf8')).entries;
const journal=path.join(root,'qa-output/nature512-r2-transfer.jsonl'),uploads=path.join(root,'qa-output/nature512-connector-upload.jsonl');
const lines=p=>fs.existsSync(p)?fs.readFileSync(p,'utf8').trim().split('\n').filter(Boolean).map(l=>JSON.parse(l)):[];
const uploaded=new Map(lines(uploads).filter(x=>x.uploaded).map(x=>[x.key,x]));
const verified=new Map(lines(journal).filter(x=>x.verified).map(x=>[x.bucket+'/'+x.key,x]));
const selected=entries.filter(e=>uploaded.has(e.key)&&verified.get(e.bucket+'/'+e.key)?.sha256!==e.sha256);
const hash=(alg,b)=>crypto.createHash(alg).update(b).digest('hex');
let next=0,finished=0;
(async()=>{await Promise.all(Array.from({length:8},async()=>{for(;;){const e=selected[next++];if(!e)return;const local=fs.readFileSync(path.join(root,e.key));if(hash('sha256',local)!==e.sha256)throw Error('Local image changed '+e.key);let method;
 if(e.bucket==='shiritori-images'){
  for(let attempt=0;;attempt++){try{const r=await fetch('https://shiritori-images.yggdrasil-learning.workers.dev/'+e.key+'?nature512='+e.sha256.slice(0,16),{signal:AbortSignal.timeout(60000)});if(!r.ok)throw Error('HTTP '+r.status);const remote=Buffer.from(await r.arrayBuffer());if(remote.length!==e.bytes||hash('sha256',remote)!==e.sha256)throw Error('Remote SHA-256 mismatch');break;}catch(err){if(attempt>=3)throw Error(e.key+': '+err.message);await new Promise(r=>setTimeout(r,1000*(attempt+1)));}}
  method='public-worker-readback-sha256';
 }else{const receipt=uploaded.get(e.key);if(receipt.etag!==hash('md5',local)||receipt.bytes!==local.length)throw Error('Private PUT integrity mismatch '+e.key);method='private-r2-put-etag-md5';}
 const record={...e,verified:true,verificationMethod:method,verifiedAt:new Date().toISOString()};fs.appendFileSync(journal,JSON.stringify(record)+'\n');verified.set(e.bucket+'/'+e.key,record);if(++finished%64===0)console.log(JSON.stringify({verifiedThisRun:finished,selected:selected.length}));
}}));
const registry=JSON.parse(fs.readFileSync(path.join(dir,'element-registry.json'),'utf8'));
const existing=registry.filter(e=>!entries.some(x=>x.key===e.image_asset));
const elementChecks=[];
for(const e of existing){
 const local=fs.readFileSync(path.join(root,e.image_asset)),expected=hash('sha256',local);
 for(let attempt=0;;attempt++){try{const r=await fetch('https://shiritori-images.yggdrasil-learning.workers.dev/'+e.image_asset+'?nature512='+expected.slice(0,16),{signal:AbortSignal.timeout(60000)});if(!r.ok)throw Error('HTTP '+r.status);const bytes=Buffer.from(await r.arrayBuffer());if(bytes.length!==local.length||hash('sha256',bytes)!==expected)throw Error('Element image mismatch');break;}catch(err){if(attempt>=3)throw err;}}
 elementChecks.push({atomicNumber:e.atomicNumber,symbol:e.symbol,key:e.image_asset,sha256:expected,verified:true});
}
fs.writeFileSync(path.join(dir,'existing-element-image-validation.json'),JSON.stringify(elementChecks,null,2)+'\n');
const report={complete:entries.every(e=>verified.get(e.bucket+'/'+e.key)?.sha256===e.sha256),publicDownloadedAndSha256Matched:entries.filter(e=>e.bucket==='shiritori-images'&&verified.get(e.bucket+'/'+e.key)?.verificationMethod==='public-worker-readback-sha256').length,privateSheetsEtagMd5Matched:entries.filter(e=>e.bucket==='shiritori-image-archive'&&verified.get(e.bucket+'/'+e.key)?.verificationMethod==='private-r2-put-etag-md5').length,totalObjects:entries.length,existingElementImagesReadbackSha256Matched:elementChecks.length};
fs.writeFileSync(path.join(dir,'r2-validation.json'),JSON.stringify(report,null,2)+'\n');
if(report.complete){
 const summary=JSON.parse(fs.readFileSync(path.join(dir,'summary.json'),'utf8'));
 Object.assign(summary,{r2VerifiedObjects:report.totalObjects,r2TransferPending:false,publicReadbackSha256Matched:report.publicDownloadedAndSha256Matched,privateSourceEtagMd5Matched:report.privateSheetsEtagMd5Matched,existingElementImagesReadbackSha256Matched:elementChecks.length});
 const plan=JSON.parse(fs.readFileSync(path.join(dir,'plan.json'),'utf8'));plan.registered=summary;plan.status='registered-delivery-verified';
 for(const [file,data] of [[path.join(dir,'summary.json'),summary],[path.join(root,'data/dictionary-imports/2026-10-19-nature512.summary.json'),summary],[path.join(dir,'plan.json'),plan]])fs.writeFileSync(file,JSON.stringify(data,null,2)+'\n');
}
console.log(JSON.stringify(report));if(process.argv.includes('--require-complete')&&!report.complete)throw Error('Not all objects have been uploaded and verified');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
