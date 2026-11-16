const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),name='2026-11-16-modern-safe';
const items=JSON.parse(fs.readFileSync(path.join(root,`data/dictionary-imports/${name}.review.json`),'utf8'));
const entries=JSON.parse(fs.readFileSync(path.join(root,`data/dictionary-imports/${name}.entries.json`),'utf8'));
const server=http.createServer((req,res)=>{
 const file=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
 if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404);return res.end();}
 res.writeHead(200,{'Content-Type':file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.json')?'application/json':'text/plain; charset=utf-8'});fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin=process.env.SHIRITORI_BASE_URL||`http://127.0.0.1:${server.address().port}`;
 const browser=await chromium.launch({headless:true,channel:'chrome'}),reports=[];
 try{
  for(const width of [1280,390,320]){
   const page=await browser.newPage({viewport:{width,height:900}}),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   await page.route('**/*',route=>!route.request().url().startsWith(origin)?route.fulfill({status:200,contentType:'application/json',body:'{}'}):route.continue());
   await page.goto(origin+'/shiritori.html');await page.waitForFunction(()=>ST.wlLoaded);
   await page.evaluate(()=>{ST.voice=false;document.getElementById('titleScreen')?.remove();});
   await page.locator('#noticeStart').click();
   const checked=await page.evaluate(async ({xs,es})=>{
    const genres=new Map(es.map(x=>[[x.reading,x.word,x.meaning].join('\t'),x.genre]));let count=0;
    for(let start=0;start<xs.length;start+=60)await Promise.all(xs.slice(start,start+60).map(async x=>{
     const row=await dictionary.reading(x.reading),i=row.words.findIndex((w,i)=>w===x.word&&row.meanings[i]===x.meaning);
     if(i<0||row.meaningLevels[i]!==x.grade||row.genres[i]!==genres.get([x.reading,x.word,x.meaning].join('\t'))||row.imagequeries[i].mode!=='none'||!row.imagequeries[i].source?.url)throw Error('Wrong payload '+x.word);count++;
    }));return count;
   },{xs:items,es:entries});
   assert.equal(checked,items.length);
   const samples=[];const categories=new Set();
   for(const x of items)if(!categories.has(x.category)){categories.add(x.category);samples.push(x);}
   for(const word of ['草','ポスト','沼','メロい','エッホエッホ','フィジカルAI','箱推し','ボンボンドロップシール']){const x=items.find(x=>x.word===word);if(x)samples.push(x);}
   for(const x of samples){
    const result=await page.evaluate(async x=>{
     ST.level=5;if(isMobile())switchMobTab('right');const row=await dictionary.reading(x.reading);await showDetail(x.reading,row);
     const v=detailView,i=v.words.findIndex((w,i)=>w===x.word&&v.meanings[i]===x.meaning);
     if(i<0)throw Error('Detail sense missing '+x.word);ST.homoIdx=i;renderDetailSlide(v.words,v.meanings,v.imgs,i,false,v.reading);
     return {text:[...document.querySelectorAll('#detContent .det-summary,#detContent .det-details')].map(el=>el.textContent).join(''),imgs:document.querySelectorAll('#detContent img').length,source:document.querySelector('.det-source a')?.href,overflow:document.documentElement.scrollWidth>innerWidth};
    },x);
    assert(result.text.includes(x.meaning),x.word);assert.equal(result.imgs,0,x.word);assert(result.source?.startsWith('https://'),x.word);assert(!result.overflow,x.word);
   }
   const endingN=await page.evaluate(async()=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;ST.level=5;syncInput('いんぷれっしょん');await submitWord();return {over:ST.gameOver,history:ST.history.map(h=>h.reading)};});
   assert(endingN.over);assert.deepEqual(endingN.history,[]);
   await page.evaluate(async()=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;ST.level=5;ST.cpuGenres=Object.keys(ShiritoriVocabulary.categories);syncInput('めろい');await submitWord();});
   await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy,{},{timeout:30000});
   const played=await page.evaluate(()=>ST.history.map(h=>({reading:h.reading,meaning:h.row.meanings[0]})));
   assert.equal(played[0].reading,'めろい');assert(played.every(x=>x.meaning));
   assert.deepEqual(errors,[]);
   const selected=items.find(x=>x.word==='メロい');await page.evaluate(async x=>{if(isMobile())switchMobTab('right');await showDetail(x.reading,await dictionary.reading(x.reading));},selected);
   const screenshots=path.join(root,'qa-output/modern-safe');fs.mkdirSync(screenshots,{recursive:true});await page.screenshot({path:path.join(screenshots,width+'.png')});
   reports.push({width,checkedSenses:checked,renderedSamples:samples.length,endingN:true,played,passed:true});await page.close();
  }
  fs.writeFileSync(path.join(root,`data/dictionary-imports/${name}.${process.env.SHIRITORI_BASE_URL?'live':'browser'}-validation.json`),JSON.stringify({local:!process.env.SHIRITORI_BASE_URL,reports},null,2)+'\n');
  console.log(JSON.stringify(reports));
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
