// All new senses and images through the actual desktop/mobile game and catalog.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/seven512-images'),data=path.join(root,'data/image-coverage/2026-10-25-seven512-images');fs.mkdirSync(out,{recursive:true});
const plan=JSON.parse(fs.readFileSync(path.join(data,'plan.json'),'utf8')),selected=plan.items;
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[],localImages=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>{const u=r.request().url();if(u.startsWith(origin)&&/\.(png|jpe?g|webp)(\?|$)/i.test(u)){localImages.push(u);return r.abort();}return u.startsWith(origin)||u.startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/')?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'});});
  if(process.env.QA_OFFLINE)await require('./shiritori-r2-fixture.cjs')(page);
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
  await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});if(width<769)await page.locator('#mobTabRight').click();
  let checked=0;
  for(const row of selected){
   await page.evaluate(async row=>{const g=lookupRow(row.reading),i=g.meanings.indexOf(row.meaning);if(i<0)throw Error('Missing meaning '+row.id);const single={...g};for(const [k,v] of Object.entries(g))if(Array.isArray(v)&&v.length===g.words.length)single[k]=[v[i]];await showDetail(row.reading,single);},row);
   await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
   assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));assert.equal(await page.locator('.det-word').innerText(),row.word);
   if(++checked%128===0)console.log(JSON.stringify({width,gameImages:checked}));
  }
  for(const reading of ['すくいなげ','まわしげり','みずでっぽう','ねこにこばん']){
   await page.evaluate(async r=>{await showDetail(r,lookupRow(r));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
   const count=await page.evaluate(()=>detailView.words.length),visited=[];
   for(let i=0;i<count;i++){visited.push(await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}
   assert.equal(new Set(visited).size,count);assert.ok(count>=2);
  }
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,'game-'+width+'.png')});
  // Verify the actual level filtering for every new meaning, including upper-level names.
  const levelErrors=await page.evaluate(items=>{const bad=[];ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);for(let level=1;level<=5;level++){ST.level=level;const pool=getPool();for(const x of items){const g=pool.find(r=>r.reading===x.reading);const found=!!g?.meanings.includes(x.meaning);if(found!==(x.grade<=level))bad.push(x.word+' '+level);}}return bad;},selected);assert.deepEqual(levelErrors,[]);
  await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
  if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
  const readings=['よりきり','せおいなげ','まわしげり','かえんほうしゃ','ぎょふのり','いそがばまわれ','ぷりんかっぷ','はさみぎろちん'];
  for(const reading of readings){await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');if(reading.endsWith('ん'))await page.waitForFunction(()=>ST.gameOver);else await page.waitForFunction(r=>ST.used.has(r),reading);await page.waitForFunction(()=>!ST.cpuBusy);}
  await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
  checked=0;
  for(const row of selected){
   await page.locator('#search').fill(row.word+' '+row.reading);let found=false;
   for(let attempt=0;attempt<100;attempt++){if((await page.locator('#asset').textContent()).includes('単語ID '+row.id+' ／')){found=true;break;}if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();}
   assert.ok(found,'Review includes '+row.word);await page.locator('#picture').evaluate(i=>i.decode());assert.equal(await page.locator('#meaning').innerText(),row.meaning);assert.ok((await page.locator('#picture').getAttribute('src')).includes('/'+row.image_asset));
   if(++checked%128===0)console.log(JSON.stringify({width,catalogImages:checked}));
  }
  await page.screenshot({path:path.join(out,'catalog-'+width+'.png')});assert.deepEqual(errors,[]);assert.deepEqual(localImages,[]);await page.close();
  results.push({width,gameImages:selected.length,catalogImages:selected.length,inputReadings:readings.length,homonymSwitching:true,gradeBands:true,realR2:!process.env.QA_OFFLINE,passed:true});console.log(JSON.stringify(results.at(-1)));
 }fs.writeFileSync(path.join(data,'browser-validation.json'),JSON.stringify({passed:true,results},null,2)+'\n');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
