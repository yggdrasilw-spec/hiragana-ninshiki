// Verify all imported meanings through the actual game's parser, level pool,
// detail rendering, homonym controls and keyboard on desktop and mobile.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'),base='data/dictionary-imports/2026-10-19-mythology512';
const items=JSON.parse(fs.readFileSync(path.join(root,base+'.review.json'),'utf8'));
const out=path.join(root,'qa-output/mythology512-browser');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
 res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8'})[path.extname(file)]||'application/octet-stream');
 fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const origin='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({headless:true,channel:'msedge'}),results=[];
 try{for(const width of [1280,390]){
  const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>route.request().url().startsWith(origin)?route.continue():route.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
  if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
  await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
  if(width<769)await page.locator('#mobTabRight').click();
  const pools=await page.evaluate(items=>[1,2,3,4,5].map(level=>{
   ST.level=level;const pool=getPool();
   const matches=items.filter(x=>pool.some(r=>r.reading===x.reading&&r.meanings.includes(x.meaning)));
   return {level,count:matches.length};
  }),items);
  assert.deepEqual(pools.map(x=>x.count),[0,0,0,0,512]);
  await page.evaluate(()=>{ST.level=5;});
  for(let offset=0;offset<items.length;offset+=128){
   const rendered=await page.evaluate(async items=>{
    for(const x of items){
     const row=lookupRow(x.reading),index=row?.meanings.indexOf(x.meaning);
     if(index<0||index===undefined||row.meaningLevels[index]!==5)throw Error('Missing grade-5 meaning '+x.word);
     const selected={...row,words:[row.words[index]],meanings:[row.meanings[index]],meaningLevels:[row.meaningLevels[index]],imagequeries:[row.imagequeries[index]]};
     await showDetail(x.reading,selected);
     await new Promise(resolve=>setTimeout(resolve,0));
     clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
     if(document.querySelector('.det-word')?.textContent!==x.word)throw Error('Wrong word '+x.word);
     if(!document.querySelector('#detContent')?.textContent.includes(x.meaning))throw Error('Wrong meaning '+x.word);
     if(document.querySelector('#detImgBox .img-main'))throw Error('Unexpected image '+x.word);
     if(!document.querySelector('#detImgBox')?.textContent.includes('せつめいだけ'))throw Error('Wrong image mode '+x.word);
    }
    return items.length;
   },items.slice(offset,offset+128));assert.equal(rendered,128);
  }
  // The old food and stationery senses keep their own grades and images.
  for(const reading of ['ぱん','のーと','がいあ']){
   await page.evaluate(async reading=>{await showDetail(reading,lookupRow(reading));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
   const count=await page.evaluate(()=>detailView.words.length),visited=[];
   for(let i=0;i<count;i++){visited.push(await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}
   assert.equal(new Set(visited).size,count);
  }
  await page.evaluate(()=>{ST.level=1;});
  assert.ok(!(await page.evaluate(()=>lookupRow('ぱん').meanings.some(m=>m.startsWith('ギリシャ神話')))));
  assert.ok((await page.evaluate(()=>lookupRow('ぱん').meanings.some(m=>m.includes('小麦粉')))));
  // Explicit advanced player entries are still recognized on an easier level.
  assert.ok((await page.evaluate(()=>lookupRow('ぜうす').meanings[0].startsWith('ギリシャ神話'))));
  await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
  if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
  for(const reading of ['ぜうす','ぐんぐにる','あめのぬぼこ','ヴァジュラ','しゅくゆう','けつぁるこあとる','あなんし']){
   await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
   await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');
   await page.waitForFunction(reading=>ST.used.has(norm(reading)),reading);await page.waitForFunction(()=>!ST.cpuBusy);
  }
  await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
  await page.locator('#kbdInput').fill('おーでぃん');await page.locator('#kbdInput').press('Enter');
  await page.waitForFunction(()=>ST.gameOver);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await page.screenshot({path:path.join(out,'game-'+width+'.png')});
  assert.deepEqual(errors,[]);results.push({width,renderedMeanings:512,pools,homonyms:true,keyboard:true,endingN:true,errors});
  await page.close();
 }
 fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,results},null,2)+'\n');
 console.log(JSON.stringify({passed:true,results}));
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(e=>{console.error(e);process.exitCode=1;server.close();});
