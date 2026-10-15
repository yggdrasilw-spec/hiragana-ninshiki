const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),name='2026-10-16-gas-vocabulary',out=path.join(root,'data/image-coverage',name);
const plan=JSON.parse(fs.readFileSync(path.join(out,'plan.json'),'utf8'));
const lines=fs.readFileSync(path.join(root,'whitelist.csv'),'utf8').trimEnd().split(/\r?\n/),head=lines.shift().split(',');
const all=lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[head[i],v]))),selected=plan.items.map(x=>({...all[x.id-1],id:x.id}));
const server=http.createServer((req,res)=>{const f=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);if(!f.startsWith(root+path.sep)||!fs.existsSync(f)||!fs.statSync(f).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8','.png':'image/png'})[path.extname(f)]||'application/octet-stream');fs.createReadStream(f).pipe(res);});
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});const results=[];
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  await page.evaluate(()=>{ST.voice=false;ST.level=3;document.getElementById('titleScreen')?.remove();switchIn('kbd');});await page.locator('#noticeStart').click();
  if(width<769)await page.locator('#mobTabRight').click();
  const checked=await page.evaluate(async rows=>{
   const failures=[];let none=0,pictures=0;
   for(const r of rows){
    const g=lookupRow(r.reading),i=g?.words.findIndex((w,i)=>w===r.word&&g.meanings[i]===r.meaning);
    if(!(i>=0)){failures.push('Parser missing '+r.id);continue;}
    const q=g.imagequeries[i];await showDetail(r.reading,{...g,words:[r.word],meanings:[r.meaning],meaningLevels:[Number(r.level)],imagequeries:[q]});
    for(let attempt=0;attempt<100;attempt++){
     const img=document.querySelector('#detImgBox .img-main');
     if(r.image_mode==='none'?document.getElementById('detImgBox').textContent.includes('せつめいだけ'):img?.src.endsWith(r.image_asset)&&img.complete&&img.naturalWidth===256)break;
     await new Promise(resolve=>setTimeout(resolve,10));
    }
    if(document.querySelector('.det-word')?.textContent!==displayStr(r.word)||!document.getElementById('detContent').textContent.includes(r.meaning.split('。')[0]))failures.push('Text '+r.id);
    const img=document.querySelector('#detImgBox .img-main');
    if(r.image_mode==='none'){none++;if(img||!document.getElementById('detImgBox').textContent.includes('せつめいだけ'))failures.push('Explanation only '+r.id);}
    else{pictures++;if(!img?.src.endsWith(r.image_asset)||img.naturalWidth!==256)failures.push('Image '+r.id);}
   }
   return {failures,none,pictures};
  },selected);assert.deepEqual(checked.failures,[]);
  // Exercise real controls across homonyms with different image policies.
  for(const reading of ['こし','おす','うら']){
   await page.evaluate(async reading=>{await showDetail(reading,lookupRow(reading));},reading);
   const count=await page.evaluate(()=>detailView.words.length);assert.ok(count>=2);
   const visited=[];
   for(let i=0;i<count;i++){visited.push(await page.locator('.det-word').innerText());assert.ok((await page.locator('.det-homo').innerText()).includes((i+1)+' / '+count));await page.locator('#detNext').click();}
   assert.ok(visited.includes(({こし:'腰',おす:'雄',うら:'浦'})[reading]),JSON.stringify(visited));
  }
  await page.evaluate(async()=>{await showDetail('るいーじ',lookupRow('るいーじ'));});await page.waitForFunction(()=>document.getElementById('detImgBox').textContent.includes('せつめいだけ'));
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:path.join(out,'game-'+width+'.png')});
  // Actual keyboard submission for corrected spellings, biological names and homonyms.
  await page.evaluate(()=>{cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
  const inputSamples=['べんき','ばね','くっきー','みじんこ','くまむし','だっこく','こし','おす','しゅうりょう','いっすんぼうし','とみか','るいーじ'];
  if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
  for(const reading of inputSamples){await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');try{await page.waitForFunction(r=>ST.used.has(r),reading);await page.waitForFunction(()=>!ST.cpuBusy);}catch(error){console.error(JSON.stringify({width,reading,state:await page.evaluate(()=>({input:ST.currentInput,used:[...ST.used],busy:ST.cpuBusy,status:document.getElementById('scMain').textContent}))}));throw error;}}
  // A real word ending in ん has an explanation but still ends the game.
  await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill('じしん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
  await page.goto(origin+'/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();await page.locator('#scope').selectOption('all');await page.locator('#sort').selectOption('dictionary');
  // Review every imported sense by exact ID; same word+reading can now have two senses.
  const catalog=await page.evaluate(async rows=>{
   const failures=[];
   for(const r of rows){
    const input=document.getElementById('search');input.value=r.word+' '+r.reading;input.dispatchEvent(new Event('input',{bubbles:true}));
    let tries=0;while(!document.getElementById('asset').textContent.includes('単語ID '+r.id+' ／')&&tries++<40){if(document.getElementById('next').disabled)break;document.getElementById('next').click();}
    if(!document.getElementById('asset').textContent.includes('単語ID '+r.id+' ／')){failures.push('ID '+r.id);continue;}
    if(document.getElementById('meaning').textContent!==r.meaning)failures.push('Meaning '+r.id);
    const img=document.getElementById('picture');
    if(r.image_mode==='none'){if(!img.hidden||!document.getElementById('imageError').textContent.includes('説明のみ'))failures.push('None '+r.id);}
    else{try{await img.decode();if(img.naturalWidth!==256||!img.getAttribute('src').startsWith(r.image_asset))failures.push('Image '+r.id);}catch{failures.push('Decode '+r.id);}}
   }
   return {failures,rows:rows.length};
  },selected);assert.deepEqual(catalog.failures,[]);assert.deepEqual(errors,[]);
  await page.screenshot({path:path.join(out,'catalog-'+width+'.png')});await page.close();results.push({width,gameWords:selected.length,catalogWords:catalog.rows,explanationOnly:checked.none,illustrated:checked.pictures,inputSamples:inputSamples.length,passed:true});console.log(JSON.stringify(results.at(-1)));
 }fs.writeFileSync(path.join(out,'browser-validation.json'),JSON.stringify({passed:true,offline:true,results},null,2)+'\n');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
