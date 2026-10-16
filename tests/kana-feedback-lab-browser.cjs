const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/kana-feedback');
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'}[path.extname(file)]||'application/octet-stream'));fs.createReadStream(file).pipe(res);});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({channel:process.env.QA_BROWSER||'chrome',headless:true});
 try{
  for(const width of [1280,390,320]){
   const page=await browser.newPage({viewport:{width,height:950}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));await page.route('https://**/*',r=>r.request().url().includes('/tf.min.js')?r.fulfill({path:path.join(root,'qa-output/word-handwriting/tf.min.js'),contentType:'text/javascript'}):r.abort());
   await page.goto(`http://127.0.0.1:${server.address().port}/kana-feedback-lab.html`);await page.waitForFunction(()=>window.KanaFeedbackLab?.getState().ready);
   assert.equal(await page.locator('[data-character]').count(),86);
   assert.equal(await page.evaluate(()=>KanaFeedbackLab.getState().char),null);
   assert.equal(await page.locator('#otherCharacters').isVisible(),false);
   const all=await page.evaluate(()=>{const out=[];for(const b of document.querySelectorAll('[data-character]')){KanaFeedbackLab.select(b.dataset.character);document.getElementById('demoCharacter').value=b.dataset.character;KanaFeedbackLab.demo('reference');const s=KanaFeedbackLab.getState();out.push({ch:s.char,n:s.reference.length,status:s.result.identity.status,advice:s.result.beauty.length+s.result.writing.length});}return out;});
   assert.equal(new Set(all.map(r=>r.ch)).size,86);for(const row of all){assert.ok(row.n);assert.equal(row.status,'unavailable');assert.equal(row.advice,0,row.ch);}
   const recognition=await page.evaluate(async()=>{document.getElementById('demoCharacter').value='く';KanaFeedbackLab.demo('reference');const ink=structuredClone(KanaFeedbackLab.getState().strokes);KanaFeedbackLab.setStrokes(ink);await KanaFeedbackLab.read();return KanaFeedbackLab.getState().candidates;});
   assert.equal(recognition.length,5);assert.ok(recognition.some(r=>r.ch==='く'),JSON.stringify(recognition));
   await page.locator('[data-candidate="く"]').click();assert.equal(await page.evaluate(()=>KanaFeedbackLab.getState().char),'く');assert.ok(await page.locator('#reference path').count());
   await page.locator('#otherCharacters summary').click();await page.locator('[data-character="ぁ"]').click();assert.equal(await page.evaluate(()=>KanaFeedbackLab.getState().char),'ぁ');
   console.log(JSON.stringify({width,actualModel:recognition,referenceCount:all.length}));
   const stale=await page.evaluate(async()=>{const {HiraganaRecognizer}=await import('./kana-recognizer.mjs?v=20261017c');const original=HiraganaRecognizer.prototype.recognize;let resolve;HiraganaRecognizer.prototype.recognize=()=>new Promise(r=>resolve=r);const pending=KanaFeedbackLab.read();document.getElementById('clear').click();resolve([{ch:'く',probability:1}]);await pending;HiraganaRecognizer.prototype.recognize=original;const state=KanaFeedbackLab.getState();return {char:state.char,busy:state.busy,candidates:state.candidates.length,strokes:state.strokes.length};});
   assert.deepEqual(stale,{char:null,busy:false,candidates:0,strokes:0});
   const referenceChecks=await page.evaluate(()=>{
    const report=[];
    for(const ch of ['く','し','つ','り','こ','き']){
     document.getElementById('demoCharacter').value=ch;KanaFeedbackLab.select(ch);KanaFeedbackLab.demo('reference');const a=KanaFeedbackLab.getState().result;
     KanaFeedbackLab.demo('reverse');const b=KanaFeedbackLab.getState().result;
     KanaFeedbackLab.demo('short');const c=KanaFeedbackLab.getState().result;
     report.push({ch,reference:{mapping:a.mapping.available,advice:a.beauty.length+a.writing.length,status:a.identity.status},reverse:b.writing.some(r=>r.id.startsWith('direction')),shortStatus:c.identity.status});
    }
    return report;
   });
   for(const row of referenceChecks){assert.equal(row.reference.mapping,true,row.ch);assert.equal(row.reference.advice,0,row.ch);assert.equal(row.reference.status,'unavailable');assert.equal(row.reverse,true,row.ch);assert.equal(row.shortStatus,'unavailable');}
   await page.locator('.demos summary').click();await page.locator('#demoCharacter').selectOption('し');await page.locator('[data-demo="wide"]').click();
   assert.ok(await page.locator('[data-rule="outline"]').count());assert.ok(await page.locator('#ink .highlight').count());assert.ok(await page.locator('#reference .highlight').count());
   assert.ok(await page.locator('#ink .direction-mark').count());assert.ok(await page.locator('#reference .direction-mark').count());
   await page.locator('#showDirections').uncheck();assert.equal(await page.locator('.direction-mark').count(),0);await page.locator('#showDirections').check();
   await page.locator('.review>summary').click();assert.doesNotMatch(await page.locator('#advice').innerText(),/外形|候補|対応|目安|相対|観察/);await page.locator('#caseKind').selectOption('error');await page.locator('#adviceRating').selectOption('useful');await page.locator('#reviewNote').fill('外形の助言を確認する作図例');
   await page.locator('#saveCase').click();assert.match(await page.locator('#savedStatus').innerText(),/1例/);
   const download=page.waitForEvent('download');await page.locator('#exportCases').click();const file=await download;
   const filename=path.join(out,`${width}-review.json`);await file.saveAs(filename);const exported=JSON.parse(fs.readFileSync(filename,'utf8'));
   assert.equal(exported.records[0].adviceRating,'useful');assert.equal(exported.records[0].evaluation.identity.status,'unavailable');assert.equal(exported.records[0].referenceSource.license,'CC BY-SA 3.0');
   await page.screenshot({path:path.join(out,`${width}.png`),fullPage:true});
   // Starting to draw replaces the explicitly labelled demo and invalidates its advice.
   await page.locator('#writing').scrollIntoViewIfNeeded();const board=await page.locator('#writing').boundingBox();
   await page.mouse.move(board.x+board.width*.3,board.y+board.height*.2);await page.mouse.down();await page.mouse.move(board.x+board.width*.4,board.y+board.height*.7,{steps:8});await page.mouse.up();
   assert.equal(await page.evaluate(()=>KanaFeedbackLab.getState().strokes.length),1);assert.equal(await page.locator('.advice-card').count(),0);assert.equal(await page.locator('#adviceRating').inputValue(),'unreviewed');
   await page.locator('#undo').click();assert.equal(await page.locator('#read').isDisabled(),true);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);
   await page.reload();await page.waitForFunction(()=>window.KanaFeedbackLab?.getState().ready);
   assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('kana-feedback-review-v1')).length),1);
   await page.goto(`http://127.0.0.1:${server.address().port}/kana-feedback-lab.html?char=%E3%81%97&demo=wide`);
   await page.waitForFunction(()=>window.KanaFeedbackLab?.getState().result);
   assert.ok(await page.locator('[data-rule="outline"]').count());
   console.log(JSON.stringify({width,referenceChecks,savedCases:1,download:true,drawing:true,overflow:false}));await page.close();
  }
  const recovery=await browser.newPage();let unavailable=true;
  await recovery.route('https://**/*',r=>r.request().url().includes('/tf.min.js')&&!unavailable?r.fulfill({path:path.join(root,'qa-output/word-handwriting/tf.min.js'),contentType:'text/javascript'}):r.abort());
  await recovery.goto(`http://127.0.0.1:${server.address().port}/kana-feedback-lab.html`);await recovery.locator('#retryModel').waitFor({state:'visible'});
  await recovery.evaluate(()=>{document.getElementById('demoCharacter').value='く';KanaFeedbackLab.demo('reference');KanaFeedbackLab.setStrokes(KanaFeedbackLab.getState().strokes);});
  await recovery.locator('#read').click();await recovery.locator('#otherCharacters').waitFor({state:'visible'});assert.equal(await recovery.evaluate(()=>KanaFeedbackLab.getState().char),null);
  unavailable=false;await recovery.locator('#retryModel').click();await recovery.waitForFunction(()=>document.getElementById('modelStatus').textContent.includes('できたよ'));
  await recovery.locator('#read').click();await recovery.locator('[data-candidate="く"]').waitFor();await recovery.close();console.log('PASS: loading failure recovery and no stale recognition after clearing.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
