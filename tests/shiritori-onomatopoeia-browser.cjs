const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const items=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-11-03-onomatopoeia2000.review.json'),'utf8'));
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
 try{
  for(const width of [1280,390,320]){
   const page=await browser.newPage({viewport:{width,height:900}}),errors=[],remote=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>{if(!route.request().url().startsWith(origin)){remote.push(route.request().url());return route.fulfill({status:200,contentType:'application/json',body:'{}'});}return route.continue();});
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});
   await page.locator('#noticeStart').click();
   const checked=await page.evaluate(async xs=>{
    let n=0;
    for(let start=0;start<xs.length;start+=50){
     await Promise.all(xs.slice(start,start+50).map(async x=>{
      const row=await dictionary.reading(x.reading),i=row.words.indexOf(x.word);
      if(i<0||row.meanings[i]!==x.meaning||row.meaningLevels[i]!==x.grade||row.genres[i]!=='onomatopoeia'||row.imagequeries[i].mode!=='none'||!row.imagequeries[i].source?.title)throw Error('Wrong payload '+x.reading);
      n++;
     }));
    }
    ST.level=3;ST.cpuGenres=['onomatopoeia'];ST.tail='き';ST.showHints=true;await dictionary.prepare('き',3,['onomatopoeia']);await renderCandidates();
    const pool=getPool();if(!pool.length||!pool.every(r=>r.genres.every(g=>g==='onomatopoeia')))throw Error('Genre pool leaked');
    syncCpuGenreUI();return {all:n,pool:pool.length};
   },items);
   assert.equal(checked.all,items.length);
   assert.equal(await page.locator('[data-genre="onomatopoeia"]').count(),1);
   assert.equal(await page.locator('#onomatopoeiaCredit a').getAttribute('href'),'data/onomatopoeia/NOTICE.md');
   for(const reading of ['きょろきょろ','うきうき','もっちり','はくしょん']){
    const x=items.find(x=>x.reading===reading);assert(x);
    const result=await page.evaluate(async r=>{await showDetail(r,lookupRow(r));return {text:document.getElementById('detContent').textContent,source:document.querySelector('.det-source a')?.href,imgs:document.querySelectorAll('#detContent img').length};},reading);
    assert(result.text.includes(x.meaning));assert(!result.text.includes('undefined'));assert(result.source?.startsWith('https://'));assert.equal(result.imgs,0);
   }
   await page.evaluate(()=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;ST.level=3;ST.cpuGenres=['onomatopoeia'];syncInput('ウキウキ');submitWord();});
   await page.waitForFunction(()=>ST.history.length>=1&&!ST.cpuBusy,{},{timeout:20000});
   const played=await page.evaluate(()=>ST.history.map(h=>({reading:h.reading,meaning:h.row.meanings[0],genre:h.row.genres[0]})));
   assert.equal(played[0].reading,'うきうき');assert(played.every(x=>x.meaning&&x.genre==='onomatopoeia'));
   const endingN=await page.evaluate(async()=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;syncInput('はくしょん');await submitWord();return {over:ST.gameOver,history:ST.history.map(h=>h.reading),cpu:ST.score.cpu};});
   assert(endingN.over);assert.deepEqual(endingN.history,[]);assert.equal(endingN.cpu,0);
   const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert(!overflow);
   assert.deepEqual(errors,[]);
   fs.mkdirSync(path.join(root,'qa-output/onomatopoeia'),{recursive:true});
   await page.screenshot({path:path.join(root,`qa-output/onomatopoeia/${width}.png`)});
   reports.push({width,checked:checked.all,genrePool:checked.pool,played,passed:true});await page.close();
  }
  fs.writeFileSync(path.join(root,'data/dictionary-imports/2026-11-03-onomatopoeia2000.browser-validation.json'),JSON.stringify({local:true,reports},null,2)+'\n');
  console.log(JSON.stringify(reports));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
