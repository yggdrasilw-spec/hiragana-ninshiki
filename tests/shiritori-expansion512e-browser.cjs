const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),dir=path.join(root,'data/image-coverage/2026-10-15-expansion512e');
const items=JSON.parse(fs.readFileSync(path.join(dir,'plan.json'),'utf8')).items;
const csv=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trim().split(/\r?\n/),header=csv.shift().split(',');
const rows=csv.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])));
const selected=items.map(x=>({...x,...rows[x.id-1]}));
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];let external=0;
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>{if(r.request().url().startsWith(origin))return r.continue();external++;return r.fulfill({status:200,contentType:'application/json',body:'{}'});});
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
  await page.locator('#noticeStart').click();if(width<769)await page.locator('#mobTabRight').click();
  const levels=await page.evaluate(items=>[1,2,3].map(level=>{ST.level=level;const pool=new Set(getPool().map(r=>r.reading));return items.filter(r=>pool.has(r.reading)!==(level===3)).map(r=>r.reading);}),selected);
  assert.ok(levels.every(x=>!x.length));await page.evaluate(()=>{ST.level=3;});
  for(const row of selected){
   await page.evaluate(async row=>{await showDetail(row.reading,lookupRow(row.reading));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},row);
   assert.equal(await page.locator('.det-word').innerText(),row.word);
   assert.ok((await page.locator('#detContent').innerText()).includes(row.meaning.split('。')[0]));
   if(row.image_asset){await page.waitForFunction(asset=>{const i=document.querySelector('#detImgBox .img-main');return i?.src.endsWith(asset)&&i.complete&&i.naturalWidth===256;},row.image_asset);}
  }
  // The image preference must not override name-card restrictions, nor may a
  // missing name card trigger image search. Test the actual fetchImg entrypoint.
  const start=external;
  const guard=await page.evaluate(async rows=>{
   ST.imagePolicy=ShiritoriImagePolicy.normalize({default:'wikimedia'});let ok=0;
   for(const r of rows){const q={ja:r.word,asset:r.image_asset,mode:'asset',credit:r.image_credit,category:'other'};const result=await fetchImg(q);if(result.url?.endsWith(r.image_asset))ok++;}
   const missing=await fetchImg({ja:'ハローキティ',asset:'assets/shiritori/expansion512e-missing.png',mode:'asset',credit:'独自文字カード（外部検索なし）',category:'other'});
   return {ok,missing:missing.url};
  },selected.filter(x=>x.image_credit==='独自文字カード（外部検索なし）'));
  assert.equal(guard.ok,360);assert.equal(guard.missing,null);assert.equal(external,start,'No external requests for all 360 cards or a missing card');
  await page.evaluate(()=>{ST.imagePolicy=ShiritoriImagePolicy.normalize(null);cpuTurn=async()=>{ST.cpuBusy=false;};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
  const samples=Object.keys(items.reduce((o,x)=>(o[x.category]=true,o),{})).map(c=>selected.find(x=>x.category===c&&!x.reading.endsWith('ん')));
  for(const row of samples){
   if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
   await page.evaluate(()=>{ST.cpuBusy=false;ST.tail='';document.getElementById('btnOk').disabled=false;});
   await page.locator('#kbdInput').fill(row.reading);await page.locator('#kbdInput').press('Enter');await page.waitForFunction(rd=>ST.used.has(rd),row.reading);
  }
  await page.evaluate(async row=>{await showDetail(row.reading,lookupRow(row.reading));},selected.find(x=>x.word.startsWith('こちら葛飾')));
  if(width<769)await page.locator('#mobTabRight').click();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:'C:/Users/user/.cache/shiritori-qa/expansion512e-'+width+'.png'});
  await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();
  await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
  for(const row of samples){
   await page.locator('#search').fill(row.word+' '+row.reading);let found=false;
   for(let n=0;n<20;n++){
    if((await page.locator('#asset').textContent()).includes('単語ID '+row.id+' ／')){found=true;break;}
    if(await page.locator('#next').isDisabled())break;await page.locator('#next').click();
   }
   assert.ok(found,'Review includes '+row.word);assert.equal(await page.locator('#meaning').innerText(),row.meaning);
   if(row.image_asset){await page.locator('#picture').evaluate(i=>i.decode());assert.equal(await page.locator('#picture').evaluate(i=>i.naturalWidth),256);}
  }
  assert.deepEqual(errors,[]);await page.close();console.log(JSON.stringify({width,passed:true,detailWords:512,cardsWithNoExternalSearch:360,inputCategories:8,reviewCategories:8}));
 }
 fs.writeFileSync(path.join(dir,'browser-validation.json'),JSON.stringify({passed:true,viewports:[1280,390],detailWordsPerViewport:512,cardsPerViewport:360,illustrationsPerViewport:152,inputCategoriesPerViewport:8,reviewCategoriesPerViewport:8,noExternalSearchForNameCards:true,missingCardFallback:true,pageErrors:0},null,2)+'\n');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
