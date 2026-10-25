const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..');
const read=file=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const items=[...read('data/dictionary-imports/2026-10-25-seven-categories.review.json'),...read('data/dictionary-imports/2026-10-25-seven-categories1024.review.json')];
assert.equal(items.length,1024);
const out=path.join(root,'qa-output/seven-categories1024');fs.mkdirSync(out,{recursive:true});
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
 res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.csv':'text/csv;charset=utf-8','.js':'text/javascript','.css':'text/css','.json':'application/json','.txt':'text/plain;charset=utf-8'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});server.keepAliveTimeout=1;
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
const browser=await chromium.launch({headless:true,channel:process.env.QA_BROWSER||'msedge'}),results=[];
try{for(const width of [1280,390]){
 const page=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
 if(await page.locator('#noticeStart').isVisible())await page.locator('#noticeStart').click();
 await page.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});
 if(width<769)await page.locator('#mobTabRight').click();
 const pools=await page.evaluate(items=>[1,2,3,4,5].map(level=>{ST.level=level;const pool=getPool();return items.filter(x=>pool.some(r=>r.reading===x.reading&&r.meanings.includes(x.meaning))).length;}),items);
 assert.deepEqual(pools,[1,2,3,4,5].map(level=>items.filter(x=>x.grade<=level).length));
 await page.evaluate(()=>{ST.level=5;});
 for(let offset=0;offset<items.length;offset+=64){
  const count=await page.evaluate(async items=>{for(const x of items){
   const row=lookupRow(x.reading),index=row?.meanings.indexOf(x.meaning);
   if(index===undefined||index<0||row.meaningLevels[index]!==x.grade)throw Error('Missing meaning or grade: '+x.word);
   const selected={...row,words:[row.words[index]],meanings:[row.meanings[index]],meaningLevels:[row.meaningLevels[index]],imagequeries:[row.imagequeries[index]]};
   await showDetail(x.reading,selected);await new Promise(r=>setTimeout(r,0));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);
   const text=Array.from(document.querySelectorAll('.det-summary,.det-details')).map(e=>e.textContent).join('');
   if(document.querySelector('.det-word')?.textContent!==x.word||text!==x.meaning)throw Error('Wrong detail: '+x.word);
   if(document.querySelector('#detImgBox .img-main')||!document.querySelector('#detImgBox')?.textContent.includes('せつめいだけ'))throw Error('Wrong image mode: '+x.word);
   if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal overflow: '+x.word);
  }return items.length;},items.slice(offset,offset+64));assert.equal(count,64);
 }
 const homonyms=[];
 for(const reading of ['すくいなげ','まわしげり','みずでっぽう','ねこにこばん']){
  await page.evaluate(async reading=>{await showDetail(reading,lookupRow(reading));clearInterval(ST.homoTimer);clearTimeout(ST.homoTimeout);},reading);
  const count=await page.evaluate(()=>detailView.meanings.length),visited=[];
  assert.ok(count>=2,'Separate real meanings: '+reading);
  for(let i=0;i<count;i++){visited.push(await page.locator('.det-summary').innerText());await page.locator('#detNext').click();}
  assert.equal(new Set(visited).size,count);homonyms.push({reading,senses:count});
 }
 // Explicit advanced entries and easy senses remain usable at their own grades.
 await page.evaluate(()=>{ST.level=2;});
 const easy=await page.evaluate(()=>lookupRow('みずでっぽう'));
 assert.ok(easy.meanings.some(m=>m.includes('おもちゃ')));assert.ok(easy.meanings.every(m=>!m.includes('ポケモン')));
 await page.evaluate(()=>{ST.level=5;cpuTurn=async()=>{ST.cpuBusy=false;updateWordBox(ST.currentInput);};ST.demoRunning=false;ST.gameOver=false;ST.moderationLocked=false;});
 if(width<769)await page.locator('#mobTabCenter').click();await page.locator('#tabKbd').click();
 const inputs=['よりきり','せおいなげ','まわしげり','かえんほうしゃ','ぎょふのり','いそがばまわれ','ぷりんかっぷ','こしなげ','せおいおとし','しょうていうち','でんこうせっか','かんぽうのまじわり','あんずるよりうむがやすし','けーきがた','ハイドロポンプ','きくはいっときのはじきかぬはいっしょうのはじ'];
 for(const reading of inputs){
  assert.ok(await page.evaluate(r=>inWhitelist(r),reading),'Input is registered: '+reading);
  await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
  await page.locator('#kbdInput').fill(reading);await page.locator('#kbdInput').press('Enter');
  await page.waitForFunction(r=>ST.used.has(norm(r)),reading);await page.waitForFunction(()=>!ST.cpuBusy);
 }
 if(width<769)await page.locator('#mobTabRight').click();
 await page.evaluate(async()=>{await showDetail('でんこうせっか',lookupRow('でんこうせっか'));});await page.waitForTimeout(30);
 await page.screenshot({path:path.join(out,'pokemon-'+width+'.png')});
 await page.evaluate(async()=>{await showDetail('あんずるよりうむがやすし',lookupRow('あんずるよりうむがやすし'));});await page.waitForTimeout(30);
 await page.screenshot({path:path.join(out,'proverb-'+width+'.png')});
 await page.evaluate(()=>{ST.tail='';ST.cpuBusy=false;ST.gameOver=false;document.getElementById('btnOk').disabled=false;});
 if(width<769)await page.locator('#mobTabCenter').click();
 await page.locator('#kbdInput').fill('はさみぎろちん');await page.locator('#kbdInput').press('Enter');await page.waitForFunction(()=>ST.gameOver);
 assert.deepEqual(errors,[]);results.push({width,renderedMeanings:1024,pools,homonyms,keyboardInputs:inputs.length,endingN:true,errors});
 console.log(JSON.stringify({width,passed:true,renderedMeanings:1024}));await page.close();
}fs.writeFileSync(path.join(out,'result.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify({passed:true,results}));
}finally{server.closeAllConnections();await browser.close();await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;server.closeAllConnections();server.close();});
