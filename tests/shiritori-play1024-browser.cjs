const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),items=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-27-play1024.review.json'),'utf8'));
const out=path.join(root,'qa-output/play1024');fs.mkdirSync(out,{recursive:true});
const real=process.argv.includes('--real-r2');
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});server.keepAliveTimeout=1;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port,browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)||(real&&r.request().url().startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/'))?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 if(!real)await require('./shiritori-r2-fixture.cjs')(page);
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});if(width<769)await page.locator('#mobTabRight').click();
 const pools=await page.evaluate(items=>[1,2,3,4,5].map(level=>{ST.level=level;const pool=getPool();return items.filter(x=>pool.some(r=>r.reading===x.reading&&r.words.some((w,i)=>w===x.word&&r.meanings[i]===x.meaning))).length;}),items);
 assert.deepEqual(pools,[1,2,3,4,5].map(level=>items.filter(x=>x.grade<=level).length));await page.evaluate(()=>ST.level=5);
 const sampleWords=['氷鬼','七並べ','ババ抜き','ポーカー','ウノ','人生ゲーム','モノポリー','カタン','オシリスの天空竜','ブラマジ','ブラック・ロータス','デュエマ','秘密戦隊ゴレンジャー','ゴレンジャー','ヒロアカ'];
 const targets=real?items.filter(x=>sampleWords.includes(x.word)):items;
 for(let offset=0;offset<targets.length;offset+=64){
  await page.evaluate(async items=>{for(const x of items){
   const row=lookupRow(x.reading),index=row?.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
   if(index===undefined||index<0||row.meaningLevels[index]!==x.grade)throw Error('Missing sense: '+x.word);
   const selected={...row,words:[row.words[index]],meanings:[row.meanings[index]],meaningLevels:[x.grade],imagequeries:[row.imagequeries[index]]};
   await showDetail(x.reading,selected);clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
   const deadline=performance.now()+15000;
   while(!document.querySelector('#detImgBox .img-main')&&performance.now()<deadline)await new Promise(r=>setTimeout(r,10));
   const img=document.querySelector('#detImgBox .img-main');if(!img)throw Error('Missing image: '+x.word);await img.decode();
   const text=Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join('');
   if(document.querySelector('.det-word')?.textContent!==x.word||text!==x.meaning)throw Error('Wrong detail: '+x.word);
   if(!img.naturalWidth||new URL(img.src).pathname.slice(1)!==x.image_asset)throw Error('Wrong asset: '+x.word);
   if(document.documentElement.scrollWidth>innerWidth)throw Error('Overflow: '+x.word);
  }},targets.slice(offset,offset+64));
  if(offset%256===0)console.log(JSON.stringify({width,shown:Math.min(offset+64,targets.length),total:targets.length,real}));
 }
 // Homonyms retain their existing meaning as well as the new game/card sense.
 for(const reading of ['すぴーど','おしりす','らー','ふらっしゅ','かるかそんぬ']){
  await page.evaluate(async reading=>{await showDetail(reading,lookupRow(reading));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
  assert.ok(await page.evaluate(()=>detailView.meanings.length)>=2,reading);
 }
 await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
 if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
 for(const word of ['氷鬼','七並べ','ババ抜き','ウノ','人生ゲーム','モノポリー','デュエマ','ブラマジ','MTG']){
  const item=items.find(x=>x.word===word);assert.ok(item);
  await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
  await page.locator('#kbdInput').fill(word==='ウノ'?word:item.reading);await page.locator('#kbdInput').press('Enter');
  try{await page.waitForFunction(r=>ST.used.has(norm(r)),item.reading);await page.waitForFunction(()=>!ST.cpuBusy);}catch(e){console.error(JSON.stringify({input:word,state:await page.evaluate(()=>({used:[...ST.used],tail:ST.tail,gameOver:ST.gameOver,cpuBusy:ST.cpuBusy,currentInput:ST.currentInput}))}));throw e;}
 }
 if(width<769)await page.locator('#mobTabRight').click();await page.evaluate(async()=>{await showDetail('こおりおに',lookupRow('こおりおに'));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);});await page.locator('#detImgBox .img-main').evaluate(i=>i.decode());await page.screenshot({path:path.join(out,'ice-tag-'+width+(real?'-r2':'')+'.png')});
 if(width<769)await page.locator('#mobTabCenter').click();await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});await page.locator('#kbdInput').fill('ぶらっくまじしゃん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);
 const catalog=await browser.newPage({viewport:{width,height:900}});await catalog.route('**/*',r=>r.request().url().startsWith(origin)||(real&&r.request().url().startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/'))?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));if(!real)await require('./shiritori-r2-fixture.cjs')(catalog);
 await catalog.goto(origin+'/shiritori-image-review.html');await catalog.locator('#message').filter({hasText:'準備できました'}).waitFor();await catalog.locator('#scope').selectOption('new');
 for(const word of sampleWords){const x=items.find(x=>x.word===word);assert(x,word);await catalog.locator('#search').fill(x.word+' '+x.reading);let found=false;
  for(let attempt=0;attempt<30;attempt++){if((await catalog.locator('#asset').textContent()).startsWith('単語ID '+x.id+' ／')){found=true;break;}if(await catalog.locator('#next').isDisabled())break;await catalog.locator('#next').click();}
  assert(found,'Catalog: '+word);assert.equal(await catalog.locator('#meaning').textContent(),x.meaning);await catalog.locator('#picture').evaluate(i=>i.decode());assert.ok(await catalog.locator('#picture').evaluate(i=>i.naturalWidth>0));
 }
 assert.ok(await catalog.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await catalog.screenshot({path:path.join(out,'catalog-'+width+(real?'-r2':'')+'.png')});
 results.push({width,meanings:targets.length,pools,keyboardInputs:9,endingN:true,catalog:sampleWords.length,errors,realR2:real});await catalog.close();await page.close();console.log(JSON.stringify({width,passed:true,real}));
}fs.writeFileSync(path.join(out,real?'result-r2.json':'result.json'),JSON.stringify({passed:true,results},null,2)+'\n');}
finally{server.closeAllConnections();await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;server.closeAllConnections();server.close();});
