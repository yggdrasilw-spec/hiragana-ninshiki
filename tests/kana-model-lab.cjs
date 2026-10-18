const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output','kana-model-lab');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
  const name=decodeURIComponent(new URL(req.url,'http://localhost').pathname),file=path.resolve(root,'.'+name);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
  const ext=path.extname(file);res.setHeader('Content-Type',({'.js':'text/javascript','.json':'application/json','.html':'text/html; charset=utf-8'})[ext]||'application/octet-stream');res.end(fs.readFileSync(file));
});
async function draw(page){await page.locator('#pad').scrollIntoViewIfNeeded();const box=await page.locator('#pad').boundingBox();await page.mouse.move(box.x+box.width*.25,box.y+box.height*.2);await page.mouse.down();await page.mouse.move(box.x+box.width*.65,box.y+box.height*.75,{steps:8});await page.mouse.up();}
function unzipStored(file){const data=fs.readFileSync(file),files=[];let offset=0;while(data.readUInt32LE(offset)===0x04034b50){const length=data.readUInt32LE(offset+18),nameLength=data.readUInt16LE(offset+26),extraLength=data.readUInt16LE(offset+28),name=data.toString('utf8',offset+30,offset+30+nameLength),start=offset+30+nameLength+extraLength;files.push({name,mimeType:name.endsWith('.bin')?'application/octet-stream':'application/json',buffer:data.subarray(start,start+length)});offset=start+length;}return files;}
let exportedFiles;
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  for(const mobile of [false,true]){
   const context=await browser.newContext({viewport:mobile?{width:390,height:844}:{width:1280,height:1000},deviceScaleFactor:mobile?3:1,acceptDownloads:true}),page=await context.newPage(),errors=[];
   page.setDefaultTimeout(60000);page.on('pageerror',e=>errors.push(e.message));
   await page.route('https://**/*',route=>route.request().url().includes('/tf.min.js')?route.fulfill({path:path.join(root,'qa-output','tf.min.js'),contentType:'text/javascript'}):route.abort());
   await page.goto(`http://127.0.0.1:${server.address().port}/handwriting-capture.html`);
   await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('１文字を書いて'));
   assert.equal(await page.locator('#testModel option').count(),2);
   await page.selectOption('#testModel','hiragana');assert.equal(await page.locator('#script').inputValue(),'hiragana');
   await page.selectOption('#testModel','katakana-marks-20261018');
   const check=await page.evaluate(async()=>{
    await tf.setBackend('cpu');await tf.ready();const results=[];
    const cv=document.createElement('canvas');cv.width=cv.height=256;const ctx=cv.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,256,256);
    const blank=KanaModels.preprocess(cv)===null;ctx.fillStyle='black';ctx.fillRect(50,60,20,120);ctx.fillRect(80,45,13,18);const pixels=KanaModels.preprocess(cv);
    for(const spec of KanaModels.models){
     const model=await KanaModels.load(spec),copy=await KanaModels.trainable(spec);
     const a=await KanaModels.predict(model,spec.labels,pixels),b=await KanaModels.predict(copy,spec.labels,pixels),m=new Map(b.map(r=>[r.label,r.score]));
     const delta=Math.max(...a.map(r=>Math.abs(r.score-m.get(r.label))));results.push({id:spec.id,classes:a.length,delta});copy.dispose();model.dispose();
    }return{blank,results};
   });
   assert.equal(check.blank,true);assert.deepEqual(check.results.map(r=>r.classes),[71,72]);for(const r of check.results)assert.ok(r.delta<.0001,JSON.stringify(r));
   await draw(page);await page.locator('#recognize').click();await page.waitForFunction(()=>document.querySelector('#prediction').textContent.includes('%'));
   await page.locator('#save').click();await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='1枚');
   await page.locator('#evaluate').click();await page.waitForFunction(()=>document.querySelector('#evaluationStatus').textContent.startsWith('比較できました'));
   assert.match(await page.locator('#evaluationResults').textContent(),/対象外 0枚/);
   await page.selectOption('#sampleUse','train');await draw(page);await page.locator('#save').click();await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='2枚');
   await draw(page);await page.locator('#save').click();await page.waitForFunction(()=>document.querySelector('#exportCount').textContent==='3枚');
   await page.locator('summary').filter({hasText:'追加学習して'}).click();await page.locator('#finetune').click();
   await page.waitForFunction(()=>document.querySelector('#trainingStatus').textContent.startsWith('完了。'),{},{timeout:120000});
   const downloadPromise=page.waitForEvent('download');await page.locator('#downloadModel').click();const download=await downloadPromise;await download.saveAs(path.join(out,mobile?'mobile-model.zip':'desktop-model.zip'));
   exportedFiles=unzipStored(path.join(out,mobile?'mobile-model.zip':'desktop-model.zip'));
   const report=JSON.parse(exportedFiles.find(f=>f.name==='training-report.json').buffer);assert.equal(report.trainIds.length,2);assert.equal(report.evaluationIds.length,1);assert.ok(report.trainIds.every(id=>!report.evaluationIds.includes(id)));
   await page.locator('#importModel').setInputFiles(exportedFiles);await page.waitForFunction(()=>document.querySelector('#prediction').textContent.includes('モデルを読み込みました'));
   await draw(page);await page.locator('#recognize').click();await page.waitForFunction(()=>document.querySelector('#prediction').textContent.includes('取込モデル')&&document.querySelector('#prediction').textContent.includes('%'));
   await page.selectOption('#set','weak');assert.ok(await page.locator('#characters button').count()>0);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
   await page.screenshot({path:path.join(out,mobile?'mobile.png':'desktop.png'),fullPage:true});assert.deepEqual(errors,[]);
   console.log(JSON.stringify({mobile,...check,lab:'passed'}));await context.close();
  }
  const page=await browser.newPage();await page.route('https://**/*',route=>route.request().url().includes('/tf.min.js')?route.fulfill({path:path.join(root,'qa-output','tf.min.js'),contentType:'text/javascript'}):route.abort());
  await require('./shiritori-r2-fixture.cjs')(page);await page.goto(`http://127.0.0.1:${server.address().port}/shiritori.html`);
  const game=await page.evaluate(async()=>{
    localStorage.setItem('shiri-katakana-model','katakana');
    ST.voice=false;await tf.setBackend('cpu');await setCharMode('katakana');const original=LABELS.length;
    const extended=LABELS.slice();await setCharMode('hiragana');const hira=LABELS.length;await setCharMode('katakana');const restored=LABELS.length;
    return{original,extended,hira,restored};
  });assert.equal(game.original,72);assert.ok(game.extended.includes('ヴ')&&game.extended.includes('ポ'));assert.equal(game.hira,71);assert.equal(game.restored,72);
  console.log(JSON.stringify({game:'passed',...game}));
  await page.locator('#modelFiles').setInputFiles(exportedFiles);await page.waitForFunction(()=>document.querySelector('#tfText').textContent==='AIにんしき OK ✓');assert.equal(await page.evaluate(()=>LABELS.length),72);
  console.log('Exported fine-tuned model reload passed in capture and game.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
