// All new meanings through the real game detail and review UI at both widths.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'data/image-coverage/2026-10-19-culture512');
const plan=JSON.parse(fs.readFileSync(path.join(out,'plan.json'),'utf8'));
const lines=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trimEnd().split('\n'),heads=lines.shift().split(',');
const rows=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
const sampleIds=new Set([...new Set(plan.items.map(x=>x.category))].map(c=>plan.items.find(x=>x.category===c).id));
for(const reading of ['もね','くろーどもね','ふきじおおどう','とーるのつち','ぶっこくじ'])sampleIds.add(plan.items.find(x=>x.reading===reading).id);
const selected=plan.items.filter(x=>process.env.QA_SAMPLE!=='1'||sampleIds.has(x.id)).map(x=>({...rows[x.id-1],id:x.id,grade:x.grade}));
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=process.env.QA_APP_ORIGIN||'http://127.0.0.1:'+server.address().port;
const artifactDir=process.env.QA_APP_ORIGIN?path.join(root,'qa-output/culture512-live'):out;fs.mkdirSync(artifactDir,{recursive:true});
const browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>{const u=r.request().url();if(u.startsWith(origin)&&/\.(png|jpe?g|webp)(\?|$)/i.test(u))throw Error('Local image fallback forbidden');return u.startsWith(origin)||u.startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/')?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'});});
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
 const gradeFailures=await page.evaluate(items=>{
  const failures=[];ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);
  for(let level=1;level<=5;level++){
   ST.level=level;const pool=new Map(getPool().map(r=>[r.reading,r]));
   for(const x of items){const row=pool.get(x.reading),present=!!row?.words.some((w,i)=>w===x.word&&row.meanings[i]===x.meaning);if(present!==(x.grade<=level))failures.push(x.word+' level '+level);}
  }
  ST.level=5;return failures;
 },selected);assert.deepEqual(gradeFailures,[]);
 if(width<769)await page.locator('#mobTabRight').click();
 for(const row of selected){
  await page.evaluate(async row=>{const group=lookupRow(row.reading),i=group.meanings.indexOf(row.meaning);if(i<0)throw Error('Missing meaning '+row.id);if(group.meaningLevels[i]!==row.grade)throw Error('Wrong grade '+row.id);await showDetail(row.reading,{...group,words:[row.word],meanings:[row.meaning],meaningLevels:[group.meaningLevels[i]],imagequeries:[group.imagequeries[i]]});},row);
  await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
  assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
  assert.equal(await page.locator('.det-word').innerText(),row.word);
 }
 // Exercise homonym switching with actual controls.
 for(const reading of ['しぼう','らぐ','ぷーま']){
  await page.evaluate(async r=>{await showDetail(r,lookupRow(r));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
  const count=await page.evaluate(()=>detailView.words.length),visited=[];
  for(let i=0;i<count;i++){visited.push(await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}
  assert.equal(new Set(visited).size,count);assert.equal(count,reading==='しぼう'?4:2);
 }
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.evaluate(async()=>{await showDetail('もね',lookupRow('もね'));});
 await page.waitForFunction(()=>{const i=document.querySelector('#detImgBox .img-main');return i?.complete&&i.naturalWidth===256;});
 await page.screenshot({path:path.join(artifactDir,'game-'+width+'.png')});
 // Real keyboard submissions; isolate the CPU reply so all selected heads can be tested.
 await page.evaluate(()=>{cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
 if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
 const readings=['かさじぞう','にほんしゅ','にほんとう','もね','くろーどもね','くまのふで','ちょうじゅうじんぶつぎが','あかずきん'];
  for(const reading of readings){await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');if(reading.endsWith('ん'))await page.waitForFunction(()=>ST.gameOver);else await page.waitForFunction(r=>ST.used.has(r),reading);await page.waitForFunction(()=>!ST.cpuBusy);}
 assert.equal(await page.evaluate(()=>ST.gameOver),true,'Ending n remains a losing move');
 await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
 await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
 for(const row of selected){
  await page.locator('#search').fill(row.word+' '+row.reading);let found=false;
  for(let attempt=0;attempt<100;attempt++){if((await page.locator('#asset').textContent()).includes('単語ID '+row.id+' ／')){found=true;break;}if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();}
  assert.ok(found,'Review includes '+row.word);await page.locator('#picture').evaluate(i=>i.decode());
  assert.equal(await page.locator('#meaning').innerText(),row.meaning);
  assert.ok((await page.locator('#picture').getAttribute('src')).includes('/'+row.image_asset));
 }
 await page.screenshot({path:path.join(artifactDir,'catalog-'+width+'.png')});assert.deepEqual(errors,[]);await page.close();
 results.push({width,gameImages:selected.length,catalogImages:selected.length,inputReadings:readings.length,homonymSwitching:true,realR2:true,passed:true});console.log(JSON.stringify(results.at(-1)));
}fs.writeFileSync(path.join(artifactDir,'browser-validation.json'),JSON.stringify({passed:true,appOrigin:origin,results},null,2)+'\n');
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
