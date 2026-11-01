const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require('C:/Users/user/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const sh=path.resolve(__dirname,'..'),en=path.resolve(sh,'../english-stage'),meta=path.join(sh,'data/integrations/english-stage-20261101'),out=path.join(sh,'qa-output/english-stage-20261101');fs.mkdirSync(out,{recursive:true});
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const catalog=read(path.join(meta,'asset-catalog.json')),plan=read(path.join(meta,'plan.json')),cards=read(path.join(en,'dist/data/grade5.json'));
const sourceServer=rawRoot=>{const root=path.resolve(rawRoot);return http.createServer((req,res)=>{const url=new URL(req.url,'http://localhost'),file=path.resolve(root,'.'+(url.pathname==='/'?'/index.html':decodeURIComponent(url.pathname)));if(!file.startsWith(root+path.sep)||!fs.existsSync(file)||!fs.statSync(file).isFile()){res.writeHead(404).end();return;}res.setHeader('Content-Type',({'.html':'text/html;charset=utf-8','.js':'text/javascript','.json':'application/json','.css':'text/css','.csv':'text/csv;charset=utf-8','.png':'image/png','.mp3':'audio/mpeg'})[path.extname(file)]||'application/octet-stream');fs.createReadStream(file).pipe(res);});};
const ss=sourceServer(sh),es=sourceServer(path.join(en,'dist'));
(async()=>{await Promise.all([new Promise(r=>ss.listen(0,'127.0.0.1',r)),new Promise(r=>es.listen(0,'127.0.0.1',r))]);const sorigin='http://127.0.0.1:'+ss.address().port,eorigin='http://127.0.0.1:'+es.address().port;
 const browser=await chromium.launch({channel:'msedge',headless:true}),results=[];
 try{
  const probe=await browser.newPage();await probe.goto(eorigin);
  const urls=[...new Set(cards.filter(c=>c.kind==='word').map(c=>c.image.url))];
  const failures=await probe.evaluate(async urls=>{let at=0;const bad=[];await Promise.all(Array.from({length:12},async()=>{while(at<urls.length){const url=urls[at++];try{const im=new Image();im.referrerPolicy='no-referrer';im.src=url;await im.decode();if(im.naturalWidth!==256)bad.push(url);}catch{bad.push(url);}}}));return bad;},urls);assert.deepEqual(failures,[]);console.log('PASS remote decode',urls.length,'unique images for',cards.filter(c=>c.kind==='word').length,'words');
  const primary=catalog.filter(c=>c.dictionaryPrimary&&c.file.startsWith('eiken-20261101'));
  for(const width of [390,1280]){
   const p=await browser.newPage({viewport:{width,height:900},reducedMotion:'reduce'}),errors=[];p.on('pageerror',e=>errors.push(e.message));
   await p.route('**/*',r=>{const u=r.request().url();return u.startsWith(sorigin)||u.startsWith('https://shiritori-images.yggdrasil-learning.workers.dev/')?r.continue():r.fulfill({status:200,contentType:'application/json',body:'{}'});});
   await p.goto(sorigin+'/shiritori.html');await p.waitForFunction(()=>ST.wlLoaded,{timeout:60000});
   if(await p.locator('#noticeStart').isVisible())await p.locator('#noticeStart').click();
   await p.evaluate(()=>{ST.voice=false;ST.level=5;document.getElementById('titleScreen')?.remove();switchIn('kbd');});if(width<769)await p.locator('#mobTabRight').click();
   for(const c of primary){
    await p.evaluate(async x=>{const full=await dictionary.reading(x.reading),i=full.meanings.indexOf(x.meaning);if(i<0)throw Error('Missing meaning '+x.id);const one={...full};for(const [k,v] of Object.entries(full))if(Array.isArray(v)&&v.length===full.words.length)one[k]=[v[i]];await showDetail(x.reading,one);},c.vocabulary);
    await p.waitForFunction(file=>{const im=document.querySelector('#detImgBox .img-main');return im?.src.endsWith('/'+file)&&im.complete&&im.naturalWidth===256;},c.file);
    assert.equal(await p.locator('.det-word').innerText(),c.vocabulary.word);
   }
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:path.join(out,'shiritori-game-'+width+'.png')});
   await p.goto(sorigin+'/shiritori-image-review.html');await p.locator('#message').filter({hasText:'準備できました'}).waitFor({timeout:60000});await p.locator('#scope').selectOption('all');await p.locator('#sort').selectOption('dictionary');
   for(const c of primary){
    await p.locator('#search').fill(c.vocabulary.word+' '+c.vocabulary.reading);let found=false;
    for(let j=0;j<100;j++){if((await p.locator('#asset').textContent()).includes('単語ID '+c.vocabulary.id+' ／')){found=true;break;}if(await p.locator('#next').isDisabled())break;await p.locator('#next').click();}
    assert(found,'catalog '+c.vocabulary.word+' '+c.vocabulary.id);assert.equal(await p.locator('#meaning').innerText(),c.vocabulary.meaning);await p.locator('#picture').evaluate(im=>im.decode());
   }
   await p.screenshot({path:path.join(out,'shiritori-catalog-'+width+'.png')});assert.deepEqual(errors,[]);await p.close();
   const q=await browser.newPage({viewport:{width,height:900}});
   for(const word of ['orange','dress','grape','foot','feet','teeth','am','in','month','hundred',"twelve o'clock"]){
    const c=cards.find(c=>c.en===word);await q.goto(eorigin+'/#card/'+c.id);await q.locator('.card-en').waitFor();assert.equal(await q.locator('.card-en').innerText(),word);await q.locator('img.picture').evaluate(im=>im.decode());assert.equal(await q.locator('img.picture').getAttribute('src'),c.image.url);assert(await q.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    if(['orange','am'].includes(word))await q.screenshot({path:path.join(out,'english-'+word+'-'+width+'.png'),fullPage:true});
   }
   await q.close();results.push({width,gameMeanings:primary.length,catalogMeanings:primary.length,englishCards:11});console.log(JSON.stringify(results.at(-1)));
  }
  const evidence={passed:true,checkedAt:new Date().toISOString(),words:cards.filter(c=>c.kind==='word').length,uniquePublicImages:urls.length,results};fs.writeFileSync(path.join(meta,'browser-validation.json'),JSON.stringify(evidence,null,2)+'\n');
 }finally{await browser.close();ss.close();es.close();}
})().catch(e=>{console.error(e);ss.close();es.close();process.exitCode=1;});
