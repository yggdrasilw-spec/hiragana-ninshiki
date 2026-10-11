const assert=require('node:assert/strict'),http=require('http'),fs=require('fs'),path=require('path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=process.env.REVIEW_ROOT||path.resolve(__dirname,'..');
const executablePath=process.env.QA_EXECUTABLE||process.env.CHROME_PATH||(process.platform==='win32'?'C:/Program Files/Google/Chrome/Application/chrome.exe':fs.existsSync('/usr/bin/chromium')?'/usr/bin/chromium':undefined);
const coverage=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/review-2026-10-10.json'),'utf8'));
const additions=JSON.parse(fs.readFileSync(path.join(root,'data/image-coverage/additional-plan-2026-10-11.json'),'utf8')).batches.flatMap(b=>b.items);
const server=http.createServer((req,res)=>{const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));if(!file.startsWith(root.replaceAll('/',path.sep)+path.sep)){res.writeHead(403).end();return;}fs.readFile(file,(e,b)=>{if(e){res.writeHead(404).end();return;}res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':file.endsWith('.css')?'text/css':file.endsWith('.png')?'image/png':'text/plain; charset=utf-8');res.end(b);});});
(async()=>{await new Promise(r=>server.listen(8959,'127.0.0.1',r));const browser=await chromium.launch({executablePath,headless:true});try{const page=await browser.newPage({viewport:{width:1000,height:950}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://127.0.0.1:8959/shiritori-image-review.html');await page.locator('#message').filter({hasText:'準備できました'}).waitFor();await page.locator('#picture').evaluate(i=>i.decode());const first=await page.locator('#word').textContent();await page.locator('#ok').click();assert.notEqual(await page.locator('#word').textContent(),first);const second=await page.locator('#word').textContent();await page.reload();await page.locator('#message').filter({hasText:'準備できました'}).waitFor();assert.equal(await page.locator('#word').textContent(),second);await page.locator('#ng').click();await page.locator('#order').fill('矢印の向きを左にしてください。\n顔を大きくしてください。');await page.reload();await page.locator('#message').filter({hasText:'準備できました'}).waitFor();assert(await page.locator('#orderForm').isVisible());assert((await page.locator('#order').inputValue()).includes('矢印'));await page.locator('#orderForm button[type=submit]').click();assert.notEqual(await page.locator('#word').textContent(),second);await page.locator('#filter').selectOption('ng');assert.equal(await page.locator('#word').textContent(),second);await page.locator('#makePrompt').click();const prompt=await page.locator('#prompt').inputValue();assert(prompt.includes('矢印の向き'));assert(prompt.includes('assets/shiritori/'));assert(prompt.includes(second));const dataPromise=page.waitForEvent('download');await page.locator('#downloadData').click();const download=await dataPromise;const saved=JSON.parse(fs.readFileSync(await download.path(),'utf8'));assert.equal(Object.values(saved.state.decisions).filter(d=>d.verdict==='ng').length,1);await page.locator('#importData').setInputFiles({name:'review.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(saved))});await page.locator('#message').filter({hasText:'件を読み込みました'}).waitFor();await page.locator('#importData').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{bad')});await page.locator('#message').filter({hasText:'読み込めませんでした'}).waitFor();await page.locator('#ok').click();assert(await page.locator('#empty').isVisible());await page.locator('#makePrompt').click();assert((await page.locator('#prompt').inputValue()).includes('修正注文はありません'));
await page.locator('#showAll').click();await page.locator('#scope').selectOption('target');assert((await page.locator('#progress').textContent()).includes(`対象 ${coverage.filter(e=>e.target&&e.image_asset).length}語`));await page.locator('#scope').selectOption('new');assert((await page.locator('#progress').textContent()).includes(`対象 ${coverage.filter(e=>['new','reused'].includes(e.assignment)&&e.image_asset).length}語`));
// Each new sense must be available in both all-images and supplemented-words views.
for(const scope of ['all','new']){
 await page.locator('#scope').selectOption(scope);
 for(const item of additions){
  const entry=coverage.find(e=>e.id===item.id);
  await page.locator('#search').fill(entry.reading);
  let found=false;
  while(true){
   const asset=await page.locator('#asset').textContent();
   if(asset.startsWith(`単語ID ${item.id} ／`)){
    assert.equal(await page.locator('#word').textContent(),entry.word);
    assert.equal(await page.locator('#meaning').textContent(),entry.meaning);
    assert.equal(await page.locator('#picture').getAttribute('src'),entry.image_asset);
    await page.locator('#picture').evaluate(i=>i.decode());
    assert(await page.locator('#picture').isVisible());
    found=true;break;
   }
   if(await page.locator('#next').isDisabled())break;
   await page.locator('#next').click();
  }
  assert(found,`New word ID ${item.id} missing in scope ${scope}`);
 }
}
await page.locator('#search').fill('後転');assert.equal(await page.locator('#word').textContent(),'後転');await page.locator('#picture').evaluate(i=>i.decode());await page.locator('#search').fill('');await page.locator('#scope').selectOption('all');if(process.env.REVIEW_POSTER)await page.screenshot({path:process.env.REVIEW_POSTER});
for(const width of [390,320]){await page.setViewportSize({width,height:844});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.locator('#ng').click();await page.locator('#order').fill('モバイルの注文');await page.locator('#orderForm button[type=submit]').click();assert(await page.locator('#word').isVisible());}
// Storage failure must keep the current word and original decision.
const word=await page.locator('#word').textContent();await page.evaluate(()=>{Storage.prototype.setItem=function(){throw Error('quota');};});await page.locator('#ok').click();assert.equal(await page.locator('#word').textContent(),word);assert((await page.locator('#message').textContent()).includes('保存できません'));assert.equal(errors.length,0,errors.join(';'));console.log('PASS: sequential OK/NG, drafts/reload/resume, prompt, JSON roundtrip, invalid import, filters, all 32 new senses in both views, mobile, storage failure');}finally{await browser.close();server.close();}})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
