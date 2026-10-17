const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const selected=JSON.parse(fs.readFileSync(path.join(root,'data/dictionary-imports/2026-10-11-school-life.review.json'),'utf8'));
const server=http.createServer((req,res)=>{
  const file=path.resolve(root,'.'+new URL(req.url,'http://localhost').pathname);
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}
  const type={'.html':'text/html; charset=utf-8','.csv':'text/csv; charset=utf-8','.txt':'text/plain; charset=utf-8'};
  res.setHeader('Content-Type',type[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;
  const browser=await chromium.launch({headless:true,executablePath:process.env.QA_EXECUTABLE||'/usr/bin/chromium'});
  try{
    for(const width of [320,390,1280]){
      const page=await browser.newPage({viewport:{width,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.route('**/*',r=>r.request().url().startsWith(origin)?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'}));
      await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
      await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});
      if(width<769)await page.locator('#mobTabRight').click();
      for(const row of selected){
        const actual=await page.evaluate(async row=>{
          const group=lookupRow(row.reading);await showDetail(row.reading,group);
          return {words:group.words,meanings:group.meanings,level:group.level};
        },row);
        assert.deepEqual(actual.words,[row.word]);assert.deepEqual(actual.meanings,[row.meaning]);
        assert.ok(await page.locator('.det-word').isVisible());
        assert.equal(await page.locator('.det-word').innerText(),row.word);
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      }
      await page.evaluate(()=>showPage('settings'));
      const source=page.locator('a[href="https://www.edrdg.org/edrdg/licence.html"]');
      await source.scrollIntoViewIfNeeded();assert.ok(await source.isVisible());
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.deepEqual(errors,[]);await page.close();
    }
    console.log(JSON.stringify({passed:true,viewports:3,importedWordsPerViewport:selected.length,sourcesAccessible:true}));
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
