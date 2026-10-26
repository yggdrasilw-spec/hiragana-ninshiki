// Download every selected PNG through the existing public read-only Worker.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root='C:/Users/user/hiragana-ninshiki',dir=root+'/data/image-coverage/2026-10-25-seven512b-images';
const inventory=JSON.parse(fs.readFileSync(dir+'/r2-upload.json','utf8'));
const entries=inventory.entries.filter(x=>x.bucket==='shiritori-images');if(entries.length!==512)throw Error('Expected512 public assets');
let next=0,done=0;const checks=[];
(async()=>{await Promise.all(Array.from({length:8},async()=>{for(;;){const x=entries[next++];if(!x)return;
 for(let attempt=0;;attempt++){try{const r=await fetch('https://shiritori-images.yggdrasil-learning.workers.dev/'+x.key+'?seven512b='+x.sha256.slice(0,16),{signal:AbortSignal.timeout(60000)});if(!r.ok)throw Error('HTTP '+r.status);const bytes=Buffer.from(await r.arrayBuffer());const hash=crypto.createHash('sha256').update(bytes).digest('hex');if(hash!==x.sha256||bytes.length!==x.bytes)throw Error('Readback mismatch '+x.key);checks.push({key:x.key,sha256:hash,bytes:bytes.length,verified:true});break;}catch(e){if(attempt>=3)throw e;await new Promise(r=>setTimeout(r,1000*(attempt+1)));}}
 if(++done%128===0)console.log(JSON.stringify({publicVerified:done,total:512}));
 }}));const report={complete:checks.length===512,publicDownloadedAndSha256Matched:checks.length,checkedAt:new Date().toISOString(),checks:checks.sort((a,b)=>a.key.localeCompare(b.key))};fs.writeFileSync(dir+'/r2-validation.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({complete:report.complete,publicDownloadedAndSha256Matched:checks.length}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
