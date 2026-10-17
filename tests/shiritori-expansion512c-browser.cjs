const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/),header=csv.shift().split(',');
const rows=csv.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
const plan=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/2026-10-15-expansion512c/plan.json'),'utf8'));
const selected=plan.items.map(x=>({...rows[x.id-1],id:x.id}));
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(path.resolve(root)+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
 await page.locator('#noticeStart').click();
 if(width<769)await page.locator('#mobTabRight').click();
 const levels=await page.evaluate(items=>[1,2,3].map(level=>{ST.level=level;const pool=new Set(getPool().map(r=>r.reading));return {level,missing:items.filter(r=>pool.has(r.reading)!==(Number(r.level)<=level)).map(r=>r.reading)};}),selected);
 assert.ok(levels.every(x=>x.missing.length===0),JSON.stringify(levels));
 await page.evaluate(()=>{ST.level=3;});
 for(const row of selected){
  await page.evaluate(async row=>{const group=lookupRow(row.reading);await showDetail(row.reading,group);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},row);
  await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
  assert.equal(await page.locator('.det-word').innerText(),row.word);assert.ok(await page.locator('#detImgBox .img-main').isVisible());
  assert.ok((await page.locator('#detImgBox .img-credit').innerText()).includes(row.image_credit));
  assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.evaluate(()=>{cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
 for(const reading of ['い','う','お','か','が','こ','じ','ず','ふ','ほ','ま','も','でじかめ','でじたるかめら','あくすた','あくりるすたんど','ますて','ますきんぐてーぷ','すくしょ','すくりーんしょっと','まいくら','まいんくらふと','えーあい','じんこうちのう','すいっちつー','にんてんどーすいっちつー']){
  if(width<769)await page.locator('#mobTabCenter').click();
  await page.locator('#tabKbd').click();
  await page.evaluate(()=>{ST.cpuBusy=false;ST.tail='';document.getElementById('btnOk').disabled=false;});
  await page.locator('#kbdInput').fill(reading);
  assert.equal(await page.evaluate(()=>ST.currentInput),reading,'Keyboard input handler is active');
  await page.locator('#kbdInput').press('Enter');
  try{await page.waitForFunction(reading=>ST.used.has(reading),reading);await page.waitForFunction(()=>!ST.cpuBusy);}
  catch(e){console.error(JSON.stringify({width,reading,state:await page.evaluate(()=>({input:ST.currentInput,kbd:document.getElementById('kbdInput').value,used:[...ST.used],cpuBusy:ST.cpuBusy,demoRunning:ST.demoRunning,gameOver:ST.gameOver,moderationLocked:ST.moderationLocked,status:document.getElementById('scMain').textContent}))}));throw e;}
 }
 await page.evaluate(async()=>{await showDetail('あくすた',lookupRow('あくすた'));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);});
 if(width<769)await page.locator('#mobTabRight').click();
 await page.screenshot({path:'C:/Users/user/.cache/shiritori-qa/expansion512c-'+width+'.png'});
 // A known expanded form ending in n is a valid dictionary entry but still
 // ends a normal game. Do not accidentally treat that as an unknown-word bug.
 if(width<769)await page.locator('#mobTabCenter').click();
 await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
 await page.locator('#kbdInput').fill('あぷりけーしょん');await page.locator('#kbdInput').press('Enter');
 await page.waitForFunction(()=>ST.gameOver);assert.ok((await page.locator('#scMain').innerText()).includes('ん'));
 console.log(JSON.stringify({width,gameWords:selected.length,passed:true}));
 await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
 await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
 for(const row of selected){
  // Exact combined word/reading avoids hundreds of unrelated matches for 品.
  await page.locator('#search').fill(row.word+' '+row.reading);let found=false;
  for(let attempt=0;attempt<100;attempt++){
   if((await page.locator('#asset').textContent()).includes('単語ID '+row.id+' ／')){found=true;break;}
   if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();
  }
  assert.ok(found,'Review catalog includes '+row.id+' '+row.word);
  await page.locator('#picture').evaluate(i=>i.decode());
  assert.equal(await page.locator('#word').innerText(),row.word);assert.equal(await page.locator('#meaning').innerText(),row.meaning);
  assert.equal(await page.locator('#picture').evaluate(i=>i.naturalWidth),256);
  assert.ok((await page.locator('#picture').getAttribute('src')).includes('/'+row.image_asset));
 }
 assert.deepEqual(errors,[]);await page.close();console.log(JSON.stringify({width,reviewWords:selected.length,passed:true}));
}const result={passed:true,wordsPerViewport:selected.length,viewports:[1280,390],game:true,reviewCatalog:true,offline:true,credits:true,levelFiltering:true,inputSamplesPerViewport:26,knownExpandedNEnding:true,pageErrors:0};
fs.writeFileSync(path.join(root,'data/image-coverage/2026-10-15-expansion512c/browser-validation.json'),JSON.stringify(result,null,2)+'\n');
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
