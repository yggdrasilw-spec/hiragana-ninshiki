const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
   const page=await browser.newPage({viewport}),requests=[],errors=[];let failPack=false;
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>{
    const url=route.request().url();requests.push(url.replace(origin,''));
    if(failPack&&url.endsWith('/japan-places/index.json'))return route.abort();
    if(!url.startsWith(origin))return route.fulfill({status:200,contentType:'application/json',body:'{}'});
    return route.continue();
   });
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   await page.locator('#noticeStart').click();await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();ST.voice=false;showPage('settings');});
   assert.ok(!requests.some(u=>u.includes('/japan-places/')),'No geography download before enabling');
   assert.equal(await page.locator('[data-genre=japanPlace]').isDisabled(),true);
   const before=requests.length;await page.locator('#japanPlacePack').check();await page.waitForFunction(()=>ST.japanPlaces&&!ST.packBusy);
   const enabled=requests.slice(before).filter(u=>u.includes('/japan-places/'));
   assert.deepEqual(enabled,['/data/shiritori-delivery/japan-places/index.json'],'Enable loads only the reading index');
   assert.equal(await page.locator('[data-genre=japanPlace]').isEnabled(),true);
   assert.equal(await page.evaluate(()=>ST.cpuGenres.includes('japanPlace')),false,'Pack and CPU choices are independent');
   const performance=await page.evaluate(()=>{const t=performance.now();const suggestions=ShiritoriVocabulary.suggestions('しんしらおが',ST.whitelist,{level:5});return {ms:performance.now()-t,target:suggestions.some(r=>r.reading==='しんしらおか'),readings:ST.whitelist.length};});assert.ok(performance.target);
   // Real ambiguous-input path retrieves the candidate's meaning without committing it.
   await page.evaluate(()=>{showPage('game');resetGame();ST.voice=false;ST.skipLinkAnimation=true;syncInput('しんしらおが');});
   await page.evaluate(()=>submitWord());assert.ok((await page.locator('#wordSuggestions').innerText()).includes('新白岡'));assert.equal(await page.evaluate(()=>ST.history.length),0);
   await page.locator('#wordSuggestions button').filter({hasText:'しんしらおか'}).click();
   await page.waitForFunction(()=>document.getElementById('detContent').textContent.includes('station_database'));
   assert.equal(await page.locator('#detContent a[href="https://creativecommons.org/licenses/by/4.0/"]').count(),1);
   // Player geography is accepted at level 1, independently of the CPU genre.
   await page.evaluate(()=>{clearWordSuggestions();ST.level=1;ST.cpuGenres=['animal'];syncInput('しんしらおか');submitWord();});
   await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:30000});
   const game=await page.evaluate(()=>ST.history.map(h=>({reading:h.reading,meaning:h.row.meanings[0],source:h.row.imagequeries[0]?.source?.title})));assert.equal(game[0].reading,'しんしらおか');assert.ok(game[0].source);
   // CPU can use exclusively the new genre, at its existing level 5.
   const cpu=await page.evaluate(async()=>{resetGame();ST.level=5;ST.cpuGenres=['japanPlace'];ST.tail='ぬ';const r=await cpuChoose();return {reading:r?.reading,genres:r?.genres,source:r?.imagequeries.map(q=>q.source?.url)};});
   assert.ok(cpu.reading?.startsWith('ぬ')&&cpu.genres.every(g=>g==='japanPlace')&&cpu.source.every(Boolean));
   // Saved choice survives reload without fetching all geography definitions.
   await page.reload();await page.waitForFunction(()=>ST.wlLoaded&&ST.japanPlaces);await page.locator('#noticeStart').click();
   await page.evaluate(()=>{document.getElementById('titleScreen')?.remove();ST.voice=false;showPage('settings');});
   assert.equal(await page.locator('#japanPlacePack').isChecked(),true);
   await page.locator('#japanPlacePack').uncheck();await page.waitForFunction(()=>!ST.japanPlaces&&!ST.packBusy);
   assert.equal(await page.evaluate(()=>inWhitelist('しんしらおか')),false);
   failPack=true;await page.locator('#japanPlacePack').click();await page.waitForFunction(()=>!ST.packBusy&&!!ST.packError);
   assert.equal(await page.evaluate(()=>ST.japanPlaces),false);assert.equal(await page.evaluate(()=>inWhitelist('りんご')),true);
   failPack=false;await page.locator('#japanPlacePack').check();await page.waitForFunction(()=>ST.japanPlaces&&!ST.packBusy);
   assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   reports.push({name,passed:true,enabledIndexBytes:fs.statSync(path.join(root,enabled[0])).size,fuzzyMs:Math.round(performance.ms),activeReadings:performance.readings,game});await page.close();
  }
  console.log(JSON.stringify(reports));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
