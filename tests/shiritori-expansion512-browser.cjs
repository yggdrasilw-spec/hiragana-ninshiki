const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split('\n');const heads=csv.shift().split(',');
const rows=csv.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[heads[i],v])));
const assigned=require('../data/image-coverage/2026-10-13-expansion512/summary.json').allIds;
const selected=assigned.map(id=>rows[id-1]);
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||undefined});
try{for(const viewport of [{width:1280,height:900},{width:390,height:844}]){
 const page=await browser.newPage({viewport});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
 if(viewport.width<500)await page.locator('#mobTabRight').click();
 for(const row of selected){
  await page.evaluate(async row=>{const group=lookupRow(row.reading);await showDetail(row.reading,group);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);const index=group.meanings.indexOf(row.meaning);if(index!==ST.homoIdx)changeDetailMeaning(index-ST.homoIdx);},row);
  if(row.image_asset)await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);
  assert.equal(await page.locator('.det-word').innerText(),row.word);if(row.image_asset)assert.ok(await page.locator('#detImgBox .img-main').isVisible());
  if(row.image_asset)assert.ok((await page.locator('#detImgBox .img-credit').innerText()).includes(row.image_credit));
  assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
 }
 assert.equal(await page.evaluate(()=>lookupRow('あり').words.length),1);
 assert.equal(await page.evaluate(()=>lookupRow('いか').words.length),2);
 assert.equal(await page.evaluate(()=>lookupRow('はるさめ').words.length),2);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.evaluate(()=>{cpuTurn=async()=>{ST.cpuBusy=false;};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
 for(const reading of ['ふかす','ぬくめる','てんじくねずみ','きる','やまとしじみ']){
  if(viewport.width<500)await page.locator('#mobTabCenter').click();
  await page.evaluate(reading=>{ST.cpuBusy=false;ST.tail='';document.getElementById('btnOk').disabled=false;setCurrentInput(reading);},reading);
  await page.locator('#kbdInput').fill(reading);
  await page.locator('#kbdInput').press('Enter');
  await page.waitForFunction(reading=>ST.used.has(reading),reading);
 }
 if(process.env.QA_OUTPUT){fs.mkdirSync(process.env.QA_OUTPUT,{recursive:true});await page.screenshot({path:path.join(process.env.QA_OUTPUT,'expansion512-'+viewport.width+'.png')});}
 await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
 await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
 for(const row of selected.filter(r=>r.image_asset).filter((r,i)=>i%16===0||['ふかす','てんじくねずみ','きらら'].includes(r.reading))){
  const id=rows.indexOf(row)+1;await page.locator('#search').fill(row.word);
  let found=false;
  for(let attempt=0;attempt<100;attempt++){
   if((await page.locator('#asset').textContent()).includes('単語ID '+id+' ／')){found=true;break;}
   if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();
  }
  assert.ok(found,'New-image review includes '+row.word);
  await page.locator('#picture').evaluate(i=>i.decode());
  assert.equal(await page.locator('#word').innerText(),row.word);
  assert.equal(await page.locator('#meaning').innerText(),row.meaning);
  assert.ok((await page.locator('#picture').getAttribute('src')).includes('/'+row.image_asset));
 }
 assert.deepEqual(errors,[]);await page.close();
}console.log(JSON.stringify({passed:true,wordsPerViewport:selected.length,viewports:2,offline:true,homonyms:true,reviewCatalog:true}));
}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
