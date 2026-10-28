const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
  res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/plain; charset=utf-8','Cache-Control':file.includes('chunks')?'max-age=31536000, immutable':'no-cache'});fs.createReadStream(file).pipe(res);
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const origin=`http://127.0.0.1:${server.address().port}`;
  const browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
  try{
    for(const [name,viewport] of [['desktop',{width:1280,height:900}],['mobile',{width:390,height:844}]]){
      const page=await browser.newPage({viewport}),requests=[],errors=[];let blockedChunk='';
      page.on('pageerror',e=>errors.push(e.message));
      await page.route('**/*',route=>{
        const url=route.request().url();requests.push(url.replace(origin,''));
        if(blockedChunk&&url.endsWith(blockedChunk))return route.abort();
        if(!url.startsWith(origin))return route.fulfill({status:200,contentType:'application/json',body:'{}'});
        return route.continue();
      });
      await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
      await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});
      await page.locator('#noticeStart').click();
      await page.waitForFunction(()=>!document.getElementById('candPills').textContent.includes('さがしています'));
      const startup=requests.filter(u=>u.includes('shiritori-delivery/'));
      assert.ok(!requests.some(u=>/whitelist\.csv|shiritori-grade-policy\.js/.test(u)),'No full dictionary/grade downloads');
      const startupBytes=startup.reduce((n,u)=>n+fs.statSync(path.join(root,u)).size,0);
      const baselineBytes=['whitelist.csv','shiritori-grade-policy.js'].reduce((n,f)=>n+fs.statSync(path.join(root,f)).size,0);
      assert.ok(startupBytes<baselineBytes*.35,'Startup dictionary bytes cut by at least 65%');
      // Hints retrieve just the needed head; the selected level/genre still filters every sense.
      const hintStart=requests.length;
      const hints=await page.evaluate(async()=>{
        ST.showHints=true;ST.tail='い';ST.level=1;ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);await renderCandidates();
        return {pills:document.querySelectorAll('#candPills .c-pill').length,head:poolHead(),valid:getPool().every(r=>r.meaningLevels.every(l=>l<=1))};
      });
      assert.ok(hints.pills>0&&hints.valid);
      const manifest=JSON.parse(fs.readFileSync(path.join(root,'data/shiritori-delivery/index.json'),'utf8'));
      assert.ok(requests.slice(hintStart).filter(u=>u.includes('/chunks/')).every(u=>manifest.chunks.some(c=>c.head==='い'&&u.endsWith(c.file))));
      await page.evaluate(()=>{ST.showHints=false;ST.tail='';});
      // An unvisited reading remains immediately valid, then fetches one payload.
      const picked=await page.evaluate(()=>{const r=ST.whitelist.find(r=>firstChar(r.reading)==='り'&&r.reading==='りんご');return {reading:r.reading,file:dictionary.manifest.chunks[r.chunk].file};});
      assert.ok(await page.evaluate(n=>inWhitelist(n),picked.reading));
      const before=requests.length;
      await page.evaluate(async n=>{await showDetail(n,lookupRow(n));},picked.reading);
      assert.equal(requests.slice(before).filter(u=>u.includes('/chunks/')).length,1);
      assert.match(await page.locator('#detContent').innerText(),/りんご|リンゴ|林檎/);
      assert.ok(!(await page.locator('#detContent').innerText()).includes('よみこんでいます'));
      // Confirm the real submit route commits complete meanings and produces a matching CPU word.
      await page.evaluate(()=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;syncInput('りんご');submitWord();});
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:20000});
      const game=await page.evaluate(()=>ST.history.map(h=>({reading:h.reading,tail:h.tailBefore,word:h.row.words[0],meaning:h.row.meanings[0],stub:!!h.row._indexOnly})));
      assert.equal(game[0].reading,'りんご');assert.equal(game[1].reading[0],game[1].tail);assert.ok(game.every(h=>h.meaning&&!h.stub));
      // Delayed old-round reads cannot commit into the next game.
      const race=await page.evaluate(async()=>{
        resetGame();ST.voice=false;syncInput('りんご');const task=submitWord();resetGame();await task;return {history:ST.history.length,busy:ST.cpuBusy};
      });assert.deepEqual(race,{history:0,busy:false});
      // Player payload failure is recoverable and never calls AI or commits a word.
      const failure=await page.evaluate(()=>{resetGame();dictionary.loaded.clear();dictionary.pool=null;const r=dictionary.index.get('りんご');return dictionary.manifest.chunks[r.chunk].file;});
      blockedChunk=failure;
      await page.evaluate(async()=>{syncInput('りんご');await submitWord();});
      assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.cpuBusy),false);
      assert.match(await page.locator('#scMain').innerText(),/よみこめません/);
      assert.equal(await page.locator('#linkMessage button').count(),1);
      blockedChunk='';await page.locator('#linkMessage button').click();
      await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:20000});
      // CPU payload failure must not award a win, and has a usable retry.
      const cpuFile=await page.evaluate(()=>{resetGame();ST.tail='り';dictionary.loaded.clear();dictionary.pool=null;return dictionary.manifest.chunks.find(c=>c.head==='り').file;});
      blockedChunk=cpuFile;await page.evaluate(()=>cpuTurn());
      assert.equal(await page.evaluate(()=>ST.gameOver),false);assert.equal(await page.evaluate(()=>ST.score.you),0);
      assert.equal(await page.evaluate(()=>ST.cpuBusy),true);assert.equal(await page.locator('#linkMessage button').count(),1);
      blockedChunk='';await page.locator('#linkMessage button').click();await page.waitForFunction(()=>ST.history.length===1&&!ST.cpuBusy,{},{timeout:20000});
      assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      reports.push({name,startupBytes,baselineBytes,reductionPercent:Math.round(100*(1-startupBytes/baselineBytes)),startupChunks:startup.length-1,passed:true});await page.close();
    }
    console.log(JSON.stringify(reports));
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
