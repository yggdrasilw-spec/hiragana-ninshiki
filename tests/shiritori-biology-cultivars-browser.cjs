const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.SHIRITORI_ROOT||path.resolve(__dirname,'..'),name='2026-10-17-biology-cultivars';
const items=[...JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/'+name+'.review.json'),'utf8')),...JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-17-snakes-danger.review.json'),'utf8'))];
const out=process.env.QA_OUTPUT||path.join(root,'qa-output',name);fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'}),results=[];
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
  await page.locator('#noticeStart').click();
  if(width<769)await page.locator('#mobTabRight').click();
  const displayed=await page.evaluate(async items=>{
   const failures=[];let photos=0;
   for(const x of items){
    const g=lookupRow(x.reading),i=g?.words.findIndex((w,i)=>w===x.word&&g.meanings[i]===x.meaning);
    if(!(i>=0)){failures.push('Missing '+x.word);continue;}
    if(g.meaningLevels[i]!==x.grade)failures.push('Grade '+x.word);
    const single={...g};for(const [key,value] of Object.entries(g))if(Array.isArray(value)&&value.length===g.words.length)single[key]=[value[i]];await showDetail(x.reading,single);
    if(document.querySelector('.det-word')?.textContent!==displayStr(x.word)||!x.meaning.split('。').filter(Boolean).every(part=>document.getElementById('detContent').textContent.includes(part)))failures.push('Rendered '+x.word);
    if(x.image_asset){
     let img;
     for(let n=0;n<100;n++){img=document.querySelector('#detImgBox .img-main');if(img?.complete&&img.naturalWidth)break;await new Promise(r=>setTimeout(r,10));}
     if(!img?.src.endsWith(x.image_asset)||!img.naturalWidth)failures.push('Saved image '+x.word);photos++;
    }
   }
   return {failures,meanings:items.length,savedImages:photos};
  },items);assert.deepEqual(displayed.failures,[]);
  const levels=await page.evaluate(items=>{
   const failures=[];ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);
   for(let level=1;level<=5;level++){
    ST.level=level;const pool=getPool();
    for(const x of items){const r=pool.find(r=>r.reading===x.reading),present=!!r?.words.some((w,i)=>w===x.word&&r.meanings[i]===x.meaning);if(present!==(x.grade<=level))failures.push(x.word+' level '+level);}
   }
   ST.level=4;
   for(const genre of ['animal','plant','food','brand']){
    ST.cpuGenres=[genre];
    if(getPool().some(r=>r.words.some((w,i)=>ShiritoriVocabulary.category(w,r.meanings[i],r.imagequeries[i].ja)!==genre)))failures.push('Genre leak '+genre);
   }
   return failures;
  },items);assert.deepEqual(levels,[]);
  // Same pronunciation remains a separate sense and gets its own photograph query.
  await page.evaluate(async()=>{ST.level=5;await showDetail('ふじ',lookupRow('ふじ'));});
  const seen=[];const homonyms=await page.evaluate(()=>detailView.words.length);
  for(let i=0;i<homonyms;i++){seen.push(await page.locator('.det-word').innerText());await page.locator('#detNext').click();}
  assert.ok(seen.includes('フジ')&&seen.includes('ふじ'));
  // An advanced rice cultivar is accepted through real controls at the easiest
  // CPU setting even when all CPU genres are disabled.
  await page.evaluate(()=>{ST.level=1;ST.cpuGenres=[];ST.tail='';ST.cpuBusy=false;ST.gameOver=false;ST.demoRunning=false;ST.moderationLocked=false;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};document.getElementById('btnOk').disabled=false;});
  if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
  for(const reading of ['せんぼんにしき','ひろけいしゅよんじゅうごごう','しばいぬ','ごーやー','しろまだら','あふりかたまごへび']){
   await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
   await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');
   await page.waitForFunction(r=>ST.used.has(r),reading);await page.waitForFunction(()=>!ST.cpuBusy);
  }
  await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
  await page.locator('#kbdInput').fill('ぽめらにあん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
  await page.evaluate(async()=>{ST.level=4;await showDetail('せんぼんにしき',lookupRow('せんぼんにしき'));});
  if(width<769)await page.locator('#mobTabRight').click();assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(out,'game-'+width+'.png')});
  await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();await page.locator('#scope').selectOption('new');await page.locator('#sort').selectOption('dictionary');
  const catalog=await page.evaluate(async items=>{
   const failures=[];
   for(const x of items){
    const s=document.getElementById('search');s.value=x.word+' '+x.reading;s.dispatchEvent(new Event('input',{bubbles:true}));
    let attempts=0;while(!document.getElementById('asset').textContent.includes('単語ID '+x.id+' ／')&&attempts++<30){if(document.getElementById('next').disabled)break;document.getElementById('next').click();}
    if(!document.getElementById('asset').textContent.includes('単語ID '+x.id+' ／')||document.getElementById('meaning').textContent!==x.meaning)failures.push(x.word);
    const picture=document.getElementById('picture');if(new URL(picture.src).pathname!=='/'+x.image_asset)failures.push('Catalog image path '+x.word);try{await picture.decode();}catch{failures.push('Catalog image load '+x.word);}if(!picture.naturalWidth)failures.push('Catalog empty '+x.word);
   }
   return {failures,meanings:items.length};
  },items);assert.deepEqual(catalog.failures,[]);assert.deepEqual(errors,[]);await page.screenshot({path:path.join(out,'catalog-'+width+'.png')});
  results.push({width,displayed,catalog,gradeBands:5,playerInputAboveLevel:true,endingNRule:true,homonyms:true});await page.close();
 }}finally{await browser.close();server.close();}
 fs.writeFileSync(path.join(out,'browser-results.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify({passed:true,results}));
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
