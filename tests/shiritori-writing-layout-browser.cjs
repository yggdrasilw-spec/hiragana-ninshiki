const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/writing-layout');
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.json':'application/json'}[path.extname(file)]||'application/octet-stream'));fs.createReadStream(file).pipe(res);});
async function seed(page){
  await page.evaluate(async()=>{
    clearCV();setCurrentInput('');
    tf={tensor4d(data,shape){return {shape,dispose(){}};}};
    tfModel={predict(input){return {data:async()=>Float32Array.from({length:input.shape[0]*71},(_,i)=>i%71===LABELS.indexOf('つ')?.99:.0001),dispose(){}};}};
    const scale=Math.min(cv.width/400,cv.height/150);
    ST.strokes=[30,130,230].map(x=>({lineWidth:4,points:[{x:x*scale,y:20*scale},{x:(x+30)*scale,y:60*scale},{x:x*scale,y:110*scale}]}));
    ST.strokes.forEach(paintStroke);await runPredict();
  });
}
async function switchMode(page,mode,height){
  if(height>500)return page.locator('#tab'+({kbd:'Kbd',btn:'Btn',canvas:'Canvas'}[mode])).click();
  await page.locator('.main-tab').nth(1).click();
  await page.locator('[data-settings-tab="input"]').click();
  await page.locator('#pageSettings .im-btn:not(.cm-btn)').nth({canvas:0,btn:1,kbd:2}[mode]).click();
  await page.locator('.main-tab').first().click();
}
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({channel:process.env.QA_BROWSER||'chrome',headless:true});const measurements=[];
try{
 for(const [width,height] of [[1366,768],[1280,720],[1101,768],[1100,768],[1024,768],[820,1180],[768,1024],[390,844],[320,740],[844,390]]){
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:width===390?2:1}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('https://**/*',r=>r.abort());await require('./shiritori-r2-fixture.cjs')(page);await page.goto(`http://127.0.0.1:${server.address().port}/shiritori.html`);
  await page.evaluate(()=>{document.getElementById('titleScreen').remove();document.querySelectorAll('dialog[open]').forEach(d=>d.close());ST.voice=false;showPage('game');switchIn('canvas');WordHandwritingUI.setMode('single');});
  await page.waitForTimeout(150);
  const single=await page.locator('#drawCanvas').boundingBox();
  assert.ok(single.height>=160,`${width} single canvas: ${single.height}`);
  assert.equal(await page.locator('#btnOk').isVisible(),true);
  await page.evaluate(()=>WordHandwritingUI.setMode('word'));await seed(page);await page.waitForTimeout(100);
  const word=await page.locator('#drawCanvas').boundingBox();
  assert.ok(word.height>=160,`${width} word canvas: ${word.height}`);
  if(width===1280)assert.ok(word.height>=260,'laptop writing height');
  if(width===390)assert.ok(word.height>=240,'phone writing height');
  if(width===820)assert.ok(word.width>700,'tablet uses its width');
  assert.equal(await page.locator('#btnOk').isVisible(),false);
  assert.equal(await page.locator('#btnSubmitWord').isVisible(),true);
  assert.equal(await page.locator('#wordPreview').innerText(),await page.locator('#wordResults button').first().innerText());
  const answer=await page.locator('#btnSubmitWord').boundingBox();
  await page.locator('#wordResults button').nth(1).focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#wordResults button').nth(1).evaluate(b=>b===document.activeElement),true,'candidate selection keeps keyboard focus');
  await page.locator('#wordResults button').first().click();
  if(height>500)assert.ok(answer.y+answer.height<=height,`${width} answer stays on screen`);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  await page.locator('#btnSubmitWord').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,`${width}x${height}-word.png`)});
  const ink=await page.locator('#drawCanvas').evaluate(c=>c.toDataURL());
  await page.locator('#btnCorrectWord').click();assert.equal(await page.locator('#wordCorrectionDialog').evaluate(d=>d.open),true);
  assert.equal((await page.locator('#drawCanvas').boundingBox()).height,word.height,'correction does not shrink ink');
  await page.locator('#wordCharacters button').first().click();
  await page.locator('#btnWordOther').click();await page.locator('#wordKanaPicker button').filter({hasText:/^し$/}).click();
  assert.equal(await page.locator('#wordCharacters button').first().innerText(),'1:し'.replace('1:',''));
  assert.equal(await page.locator('#drawCanvas').evaluate(c=>c.toDataURL()),ink,'correction preserves actual writing');
  await page.screenshot({path:path.join(out,`${width}x${height}-correction.png`)});
  await page.locator('#btnInspectFromCorrection').click();assert.equal(await page.locator('#handwritingReviewDialog').evaluate(d=>d.open),true);
  await page.locator('#btnCharacterReplay').click();await page.locator('#btnReviewClose').click();
  await page.locator('#btnCloseWordCorrection').click();assert.equal(await page.locator('#writingTools').evaluate(d=>d.open),false,'character inspection leaves the canvas unobstructed');
  const candidate=await page.locator('#wordPreview').innerText();
  await page.locator('#btnBackspace').click();assert.equal(await page.locator('#wordPreview').innerText(),candidate.slice(0,-1));
  if(width===1366){
    const before=await page.locator('#wordPreview').innerText();
    await page.locator('#btnWritingFocus').click();await page.waitForTimeout(150);
    assert.ok((await page.locator('#drawCanvas').boundingBox()).width>word.width);
    assert.equal(await page.locator('#wordPreview').innerText(),before,'enlargement preserves corrected candidate');
    await page.locator('#btnWritingFocus').click();await page.waitForTimeout(100);
    assert.equal(await page.locator('#wordPreview').innerText(),before);
  }
  if(width===390){
    const before=await page.locator('#wordPreview').innerText();await page.setViewportSize({width:844,height:390});await page.waitForTimeout(150);
    assert.equal(await page.locator('#wordPreview').innerText(),before,'rotation preserves corrected candidate');
    assert.ok((await page.locator('#drawCanvas').boundingBox()).height>=160);
    await page.setViewportSize({width,height});await page.waitForTimeout(100);
  }
  await switchMode(page,'kbd',height);assert.equal(await page.locator('#btnOk').isVisible(),true);assert.equal(await page.locator('#btnSubmitWord').isVisible(),false);
  await page.locator('#kbdInput').fill('くし');assert.equal(await page.evaluate(()=>ST.currentInput),'くし');
  await switchMode(page,'btn',height);assert.equal(await page.locator('#modeBtn').isVisible(),true);
  await switchMode(page,'canvas',height);await page.waitForTimeout(100);
  if(width===1366){
    await page.locator('#btnWritingFocus').click();await page.locator('#tabBtn').click();
    assert.equal(await page.evaluate(()=>document.body.classList.contains('writing-focus')),false,'switching input exits focused writing');
    assert.equal(await page.locator('#topbar').isVisible(),true);await page.locator('#tabCanvas').click();
  }
  if(width<=1100||height<=500){
    await page.locator('#mobTabLeft').click();assert.equal(await page.locator('#colLeft').isVisible(),true);
    await page.locator('#mobTabRight').click();assert.equal(await page.locator('#colRight').isVisible(),true);
    await page.locator('#mobTabCenter').click();assert.equal(await page.locator('#drawCanvas').isVisible(),true);
  }
  assert.deepEqual(errors,[],`${width} page errors`);measurements.push({width,height,single,word,answer});await page.close();
 }
 fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(measurements,null,2));console.log(JSON.stringify(measurements));console.log('Writing layout browser checks passed.');
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
