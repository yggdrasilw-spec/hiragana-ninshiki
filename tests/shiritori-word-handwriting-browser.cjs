const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),http=require('node:http');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'qa-output/word-handwriting');
const fixtures=require('./fixtures/shiritori-word-strokes.cjs');
const server=http.createServer((req,res)=>{
  const filename=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
  if(!filename.startsWith(root+path.sep)||!fs.existsSync(filename)||!fs.statSync(filename).isFile()){res.writeHead(404);return res.end();}
  res.setHeader('Content-Type',({'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'}[path.extname(filename)]||'application/octet-stream'));
  fs.createReadStream(filename).pipe(res);
});
(async()=>{
  await new Promise(r=>server.listen(0,'127.0.0.1',r));fs.mkdirSync(out,{recursive:true});
  const origin=`http://127.0.0.1:${server.address().port}`,browser=await chromium.launch({channel:process.env.QA_BROWSER||'chrome',headless:true});
  try{
    for(const width of (process.env.QA_WIDTHS||'1280,820,390,320').split(',').map(Number)){
      const page=await browser.newPage({viewport:{width,height:width===820?700:900},deviceScaleFactor:width===390?2:1}),errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      await page.route('https://**/*',route=>{
        if(route.request().url().includes('/tf.min.js')&&fs.existsSync(path.join(out,'tf.min.js')))return route.fulfill({path:path.join(out,'tf.min.js'),contentType:'text/javascript'});
        return route.abort();
      });
      await require('./shiritori-r2-fixture.cjs')(page);await page.goto(origin+'/shiritori.html');
      await page.evaluate(()=>{document.getElementById('titleScreen').remove();document.querySelectorAll('dialog[open]').forEach(d=>d.close());ST.voice=false;resizeCV();});
      assert.equal(await page.evaluate(()=>ST.handwritingMode),'single');
      await page.evaluate(()=>{document.querySelectorAll('dialog[open]').forEach(d=>d.close());showPage('settings');setSettingsTab('input');});
      await page.locator('#enableWordHandwriting').check();
      assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('shiri-settings')).handwritingMode),'word');
      await page.reload();
      await page.evaluate(()=>{document.getElementById('titleScreen').remove();document.querySelectorAll('dialog[open]').forEach(d=>d.close());ST.voice=false;resizeCV();});
      assert.equal(await page.evaluate(()=>ST.handwritingMode),'word');
      assert.equal(await page.locator('#enableWordHandwriting').isChecked(),true);
      const real=await page.evaluate(async()=>{
        if(typeof tf==='undefined')return {skipped:'TensorFlow.js fixture missing'};
        await loadModelUrl(MODEL_PATH.hiragana);
        if(!tfModel)throw Error('real model failed to load');
        function line(points){return {points:points.map(([x,y])=>({x,y})),lineWidth:4};}
        ST.strokes=[line([[70,20],[30,70],[70,120]]),line([[190,20],[150,70],[190,120]])];
        await runPredict();
        const candidates=[...document.querySelectorAll('#wordResults button')].map(b=>b.textContent);
        const snapshot=document.createElement('canvas');snapshot.width=64;snapshot.height=64;
        const arrays=ShiritoriWordHandwriting.plan(ST.strokes).segments.map(s=>WordHandwritingUI.rasterize(s));
        // Display width is not part of the recognition image.
        ST.strokes.forEach(s=>s.lineWidth=30);
        const same=ShiritoriWordHandwriting.plan(ST.strokes).segments.every((s,i)=>WordHandwritingUI.rasterize(s).every((v,j)=>v===arrays[i][j]));
        clearCV();return {candidates,same,backend:tf.getBackend()};
      });
      if(process.env.REQUIRE_REAL_MODEL==='1')assert.ok(!real.skipped,'real model required');
      if(!real.skipped){assert.ok(real.candidates.includes('くく'),JSON.stringify(real));assert.equal(real.same,true);}
      if(!real.skipped&&width===1280){
        const baseline=[];
        for(const word of fixtures.words){
          const result=await page.evaluate(async strokes=>{
            clearCV();ST.strokes=strokes;const start=performance.now();await runPredict();
            return {candidates:[...document.querySelectorAll('#wordResults button')].map(b=>b.textContent),milliseconds:Math.round(performance.now()-start)};
          },fixtures.sample(word));
          baseline.push({expected:word,...result});
        }
        fs.writeFileSync(path.join(out,'geometric-baseline.json'),JSON.stringify(baseline,null,2));
        console.log(JSON.stringify({geometricBaseline:baseline}));
      }
      // Draw two letters with real pointer events; no recognition button is pressed.
      await page.evaluate(()=>{clearCV();showPage('game');resizeCV();});
      await page.locator('#drawCanvas').scrollIntoViewIfNeeded();const board=await page.locator('#drawCanvas').boundingBox();
      for(const x of [.25,.65]){await page.mouse.move(board.x+board.width*(x+.06),board.y+board.height*.2);await page.mouse.down();await page.mouse.move(board.x+board.width*(x-.06),board.y+board.height*.5,{steps:5});await page.mouse.move(board.x+board.width*(x+.06),board.y+board.height*.8,{steps:5});await page.mouse.up();}
      await page.waitForFunction(()=>document.querySelectorAll('#wordCharacters button').length>=2);
      assert.ok(await page.locator('#handwritingBounds g').count()>=2);console.log(JSON.stringify({width,automaticRecognition:true}));
      await page.evaluate(()=>{WordHandwritingUI.setMode('single');});assert.equal(await page.locator('#enableWordHandwriting').isChecked(),false);
      await page.evaluate(()=>{WordHandwritingUI.setMode('word');});
      const checks=await page.evaluate(async()=>{
        clearCV();setCurrentInput('');
        const actualTf=typeof tf==='undefined'?null:tf,actualModel=tfModel,actualWhitelist=ST.whitelist;
        ST.whitelist=[];
        let disposed=0;
        // Deterministic classifier isolates candidate editing/state from model accuracy.
        tf={tensor4d(data,shape){return {shape,dispose(){disposed++;}};}};
        tfModel={predict(input){return {data:async()=>Float32Array.from({length:input.shape[0]*71},(_,i)=>i%71===LABELS.indexOf('つ')?.99:.0001),dispose(){disposed++;}};}};
        const points=[[[30,20],[65,65],[30,110]],[[125,55],[145,75],[125,100]]];
        ST.strokes=points.map(pts=>({points:pts.map(([x,y])=>({x,y})),lineWidth:4}));
        clearCV(false);ST.strokes.forEach(paintStroke);invalidatePrediction();
        await runPredict();
        if(!document.querySelector('#wordResults button'))throw Error('no word candidates');
        const chars=[...document.querySelectorAll('#wordCharacters button')].map(b=>b.textContent);
        const boxes=[...document.querySelectorAll('#handwritingBounds g')].map(g=>({number:Number(g.dataset.segment),ch:g.dataset.character}));
        const pixels=cv.toDataURL();
        const overlay=document.getElementById('handwritingBounds').getBoundingClientRect(),canvas=cv.getBoundingClientRect();
        const aligned=['x','y','width','height'].every(k=>Math.abs(overlay[k]-canvas[k])<1);
        document.querySelectorAll('#wordResults button')[1].click();
        const alternateBoxes=[...document.querySelectorAll('#handwritingBounds g')].map(g=>g.dataset.character).join('');
        const alternateText=[...document.querySelectorAll('#wordCharacters button')].map(b=>b.textContent).join('');
        document.querySelector('#wordResults button').click();
        const overlayDoesNotChangeInk=pixels===cv.toDataURL();
        document.querySelectorAll('#wordCharacters button')[1].click();
        const highlighted=document.querySelector('#handwritingBounds g.selected')?.dataset.segment==='2';
        const before=document.querySelectorAll('#wordCharacters button')[1].textContent;
        document.getElementById('btnWordSmall').click();
        const after=document.querySelectorAll('#wordCharacters button')[1].textContent;
        const otherBefore=[...document.querySelectorAll('#wordResults button')].slice(1).map(b=>b.textContent);
        document.querySelector('#wordCharacters button').click();document.getElementById('btnWordOther').click();
        [...document.querySelectorAll('#wordKanaPicker button')].find(b=>b.textContent==='し').click();
        const pickerWorked=document.querySelector('#wordCharacters button').textContent==='し';
        const otherAfter=[...document.querySelectorAll('#wordResults button')].slice(1).map(b=>b.textContent);
        document.getElementById('btnWordOther').click();
        [...document.querySelectorAll('#wordKanaPicker button')].find(b=>b.textContent==='つ').click();
        document.getElementById('btnAcceptWord').click();
        const accepted=ST.currentInput,strokesAfter=ST.strokes.length;
        const event=(x,y)=>({clientX:cv.getBoundingClientRect().left+x,clientY:cv.getBoundingClientRect().top+y,pointerId:7,button:0,preventDefault(){}});
        const capture=cv.setPointerCapture;cv.setPointerCapture=()=>{};
        beginStroke(event(20,20));moveStroke(event(50,90));endStroke(event(50,90));
        const readEnabled=!document.getElementById('btnReadWord').disabled;
        let resolve;
        tfModel={predict(input){return {data:()=>new Promise(r=>resolve=()=>r(Float32Array.from({length:input.shape[0]*71},(_,i)=>i%71===0?1:0))),dispose(){disposed++;}};}};
        const pending=runPredict();clearCV();resolve();await pending;
        const stale=document.querySelectorAll('#wordResults button').length;
        const clearedBoxes=document.querySelectorAll('#handwritingBounds g').length===0;
        const readDisabled=document.getElementById('btnReadWord').disabled;
        // Switch away while inference is pending.
        beginStroke(event(20,20));moveStroke(event(50,90));endStroke(event(50,90));
        const pendingMode=runPredict();WordHandwritingUI.setMode('single');resolve();await pendingMode;
        const legacyVisible=!document.getElementById('predRow').classList.contains('hidden');
        const noStale=document.querySelectorAll('#wordResults button').length===0;
        WordHandwritingUI.setMode('word');ST.charMode='katakana';WordHandwritingUI.sync();
        const katakanaFallback=!WordHandwritingUI.active()&&!document.getElementById('predRow').classList.contains('hidden');
        ST.charMode='hiragana';WordHandwritingUI.sync();
        const restored=WordHandwritingUI.active();
        cv.setPointerCapture=capture;tf=actualTf;tfModel=actualModel;ST.whitelist=actualWhitelist;invalidatePrediction();
        return {chars,boxes,aligned,alternateBoxes,alternateText,overlayDoesNotChangeInk,highlighted,clearedBoxes,before,after,pickerWorked,otherBefore,otherAfter,accepted,strokesAfter,readEnabled,stale,readDisabled,legacyVisible,noStale,katakanaFallback,restored,disposed};
      });
      assert.notEqual(checks.before,checks.after);assert.match(checks.accepted,/^[つっ]{2}$/);assert.equal(checks.strokesAfter,0);
      assert.equal(checks.pickerWorked,true);assert.deepEqual(checks.otherBefore,checks.otherAfter,'editing a candidate must not change other candidates');
      for(const key of ['readEnabled','readDisabled','legacyVisible','noStale','katakanaFallback','restored'])assert.equal(checks[key],true,key);
      assert.equal(checks.stale,0);assert.ok(checks.disposed>=6);
      assert.deepEqual(checks.boxes,checks.chars.map((ch,i)=>({number:i+1,ch})));
      assert.equal(checks.alternateBoxes,checks.alternateText);
      for(const key of ['aligned','overlayDoesNotChangeInk','highlighted','clearedBoxes'])assert.equal(checks[key],true,key);
      const dictionary=await page.evaluate(async()=>{
        const saved={tf,model:tfModel,whitelist:ST.whitelist,genres:ST.cpuGenres};
        try{
          clearCV();setCurrentInput('く');ST.cpuGenres=[];
          ST.whitelist=[{reading:'くし',words:['くし'],meanings:['テスト'],imagequeries:[{ja:'くし'}],level:4}];
          tf={tensor4d(data,shape){return {shape,dispose(){}};}};tfModel={predict(input){return {data:async()=>Float32Array.from({length:input.shape[0]*71},(_,i)=>i%71===LABELS.indexOf('あ')?.8:i%71===LABELS.indexOf('し')?.2:.00001),dispose(){}};}};
          ST.strokes=[{points:[{x:20,y:20},{x:40,y:80}],lineWidth:4}];await runPredict();
          return {first:document.querySelector('#wordResults button').textContent,known:document.querySelector('#wordResults button').dataset.known,answer:document.getElementById('btnSubmitWord').textContent};
        }finally{tf=saved.tf;tfModel=saved.model;ST.whitelist=saved.whitelist;ST.cpuGenres=saved.genres;clearCV();setCurrentInput('');}
      });
      assert.deepEqual(dictionary,{first:'し',known:'true',answer:'「くし」で こたえる'});
      const modelRace=await page.evaluate(async()=>{
        const originalTf=tf,originalModel=tfModel;let oldReady,newReady,oldDisposed=0;
        const newer={predict(){return {data:async()=>[],dispose(){}};},dispose(){}};
        tf={zeros(){return {dispose(){}};},loadLayersModel(url){return new Promise(resolve=>{if(url==='old')oldReady=resolve;else newReady=resolve;});}};
        try{
          const old=loadModelUrl('old'),next=loadModelUrl('new');newReady(newer);await next;
          oldReady({dispose(){oldDisposed++;}});await old;
          return {latest:tfModel===newer,oldDisposed};
        }finally{tf=originalTf;tfModel=originalModel;invalidatePrediction();WordHandwritingUI.sync();}
      });
      assert.deepEqual(modelRace,{latest:true,oldDisposed:1});
      const review=await page.evaluate(async()=>{
        clearCV();
        ST.strokes=[[[20,20],[80,80]],[[150,80],[110,20]],[[40,10],[47,17]]].map(pts=>({lineWidth:4,points:pts.map(([x,y])=>({x,y}))}));
        clearCV(false);ST.strokes.forEach(paintStroke);const ink=cv.toDataURL();
        HandwritingReview.setEnabled(true);
        const ungroupedNumberCount=document.querySelectorAll('#handwritingProcess .stroke-order').length;
        HandwritingReview.update([{ch:'が',segment:{strokes:[ST.strokes[2],ST.strokes[0]]}},{ch:'く',segment:{strokes:[ST.strokes[1]]}}],0);
        const order=[...document.querySelectorAll('#handwritingProcess .stroke-order')].map(n=>n.textContent);
        const arrows=document.querySelectorAll('#handwritingProcess .stroke-direction').length;
        document.getElementById('btnStrokeReplay').click();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        const replayStarted=!!document.querySelector('#handwritingProcess .replay-background');
        document.getElementById('btnStrokeReplay').click();
        const replayStopped=!document.querySelector('#handwritingProcess .replay-background');
        document.getElementById('btnInspectCharacter').click();
        const dialog=document.getElementById('handwritingReviewDialog');
        const dialogOpened=dialog.open;
        const localOrder=[...document.querySelectorAll('#characterReviewSvg .stroke-order')].map(n=>n.textContent);
        document.getElementById('btnCharacterReplay').click();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        const characterReplay=!!document.querySelector('#characterReviewSvg .replay-background');
        document.getElementById('btnReviewClose').click();
        const closed=!dialog.open;
        HandwritingReview.setEnabled(false);
        const off=document.querySelectorAll('#handwritingProcess > *').length===0&&document.getElementById('btnStrokeReplay').hidden;
        const savedOff=JSON.parse(localStorage.getItem('shiri-settings')).showHandwritingProcess===false;
        const noInkChanges=ink===cv.toDataURL();
        HandwritingReview.setEnabled(true);
        document.getElementById('btnInspectCharacter').click();document.getElementById('btnCharacterReplay').click();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        HandwritingReview.setEnabled(false);
        const offClosesReplay=!dialog.open&&!document.querySelector('#handwritingProcess .replay-background');
        HandwritingReview.setEnabled(true);
        document.getElementById('btnStrokeReplay').click();
        await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
        const capture=cv.setPointerCapture;cv.setPointerCapture=()=>{};
        const box=cv.getBoundingClientRect(),ev={clientX:box.left+40,clientY:box.top+60,pointerId:9,button:0,preventDefault(){}};
        beginStroke(ev);endStroke(ev);invalidatePrediction();cv.setPointerCapture=capture;
        const newInkStopsReplay=!document.querySelector('#handwritingProcess .replay-background');
        clearCV();
        const cleared=document.querySelectorAll('#handwritingProcess > *').length===0;
        return {ungroupedNumberCount,order,arrows,replayStarted,replayStopped,dialogOpened,localOrder,characterReplay,closed,off,savedOff,noInkChanges,offClosesReplay,newInkStopsReplay,cleared};
      });
      assert.equal(review.ungroupedNumberCount,0);assert.deepEqual(review.order,['1','1','2']);assert.deepEqual(review.localOrder,['1','2']);assert.equal(review.arrows,3);
      for(const key of ['replayStarted','replayStopped','dialogOpened','characterReplay','closed','off','savedOff','noInkChanges','offClosesReplay','newInkStopsReplay','cleared'])assert.equal(review[key],true,key);
      await page.evaluate(strokes=>{
        showPage('game');switchIn('canvas');resizeCV();setCurrentInput('');
        const scale=Math.min((cv.width-24)/335,(cv.height-44)/110);
        ST.strokes=strokes.map(s=>({...s,lineWidth:calcLineW(),points:s.points.map(p=>({x:12+p.x*scale,y:28+p.y*scale}))}));
        clearCV(false);ST.strokes.forEach(paintStroke);
      },fixtures.sample('りんご'));
      if(!real.skipped)await page.evaluate(()=>runPredict());
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
      assert.equal(overflow,false,`no horizontal overflow at ${width}`);assert.deepEqual(errors,[]);
      await page.screenshot({path:path.join(out,`${width}.png`),fullPage:true});
      if(!real.skipped){
        await page.locator('#wordCharacters button').first().click();await page.locator('#btnInspectCharacter').click();
        await page.screenshot({path:path.join(out,`${width}-character-review.png`),fullPage:true});
        await page.locator('#btnReviewClose').click();
      }
      if(!real.skipped){
        await page.emulateMedia({reducedMotion:'reduce'});
        await page.evaluate(strokes=>{resetGame();ST.voice=false;ST.skipLinkAnimation=true;getCpuDelay=()=>80;HandwritingReview.setEnabled(false);switchIn('canvas');ST.strokes=strokes;clearCV(false);ST.strokes.forEach(paintStroke);},fixtures.sample('くし'));
        await page.evaluate(()=>runPredict());
        assert.equal(await page.locator('#wordResults button').first().innerText(),'くし');assert.equal(await page.locator('#wordResults button').first().getAttribute('data-known'),'true');
        if(width<=390)assert.ok((await page.locator('#btnSubmitWord').boundingBox()).width>220,'wide answer button');
        assert.equal(await page.locator('#btnOk').evaluate(b=>b.scrollWidth<=b.clientWidth),true,'answer label fits');
        await page.locator('#btnSubmitWord').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(out,`${width}-answer-ready.png`),fullPage:true});
        await page.locator('#btnSubmitWord').click();await page.waitForFunction(()=>ST.history.length>=2&&!ST.cpuBusy);
        const turn=await page.evaluate(()=>({first:ST.history[0].reading,speaker:ST.history[0].speaker,next:ST.history[1].speaker,used:ST.used.has('くし'),you:ST.score.you,cpu:ST.score.cpu,ink:ST.strokes.length,input:ST.currentInput}));
        assert.deepEqual(turn,{first:'くし',speaker:'あなた',next:'CPU',used:true,you:1,cpu:1,ink:0,input:''});
        // The direct answer still obeys the normal shiritori connection rule.
        await page.evaluate(strokes=>{resetGame();ST.tail='あ';ST.strokes=strokes;clearCV(false);ST.strokes.forEach(paintStroke);},fixtures.sample('くし'));await page.evaluate(()=>runPredict());
        await page.locator('#btnSubmitWord').click();await page.waitForFunction(()=>!ST.cpuBusy);
        assert.equal(await page.evaluate(()=>ST.history.length),0);assert.equal(await page.evaluate(()=>ST.currentInput),'くし');
        console.log(JSON.stringify({width,dictionary,fullGameTurn:turn,normalValidation:true}));
        await page.evaluate(()=>HandwritingReview.setEnabled(true));
      }
      console.log(JSON.stringify({width,real,checks,review}));
      await page.reload();assert.equal(await page.evaluate(()=>ST.showHandwritingProcess),true,'review preference persists');
      await page.close();
    }
    console.log('Word handwriting browser checks passed.');
  }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1;});
