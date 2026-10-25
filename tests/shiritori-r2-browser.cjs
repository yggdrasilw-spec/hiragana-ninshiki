// End-to-end test against real Workers delivery, with local image requests denied.
const assert = require('node:assert/strict'), fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assets = require('../shiritori-assets.js');
const root = path.resolve(__dirname, '..'), out = path.join(root, 'qa-output/r2');
const localImages = [];
const server = http.createServer((req, res) => {
  const key = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).slice(1);
  if (/\.(png|jpe?g|webp|gif|svg)$/i.test(key)) { localImages.push(key); res.writeHead(404).end(); return; }
  const file = path.resolve(root, key || 'shiritori.html');
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404).end(); return; }
  res.setHeader('Content-Type', ({ '.html': 'text/html;charset=utf-8', '.js': 'text/javascript', '.json': 'application/json', '.csv': 'text/csv;charset=utf-8', '.css': 'text/css', '.txt': 'text/plain;charset=utf-8', '.wav': 'audio/wav' })[path.extname(file)] || 'application/octet-stream');
  fs.createReadStream(file).pipe(res);
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = process.env.QA_APP_ORIGIN || 'http://127.0.0.1:' + server.address().port;
  const browser = await chromium.launch({ headless: true, channel: 'msedge' });
  fs.mkdirSync(out, { recursive: true });
  const results = [];
  try {
    for (const [name, width, height] of [['desktop', 1280, 900], ['mobile', 390, 844]]) {
      const page = await browser.newPage({ viewport: { width, height }, reducedMotion: 'reduce' });
      const errors = [], delivered = new Set();
      page.on('pageerror', e => errors.push(e.message));
      page.on('response', response => { if (response.url().startsWith(assets.origin) && response.ok()) delivered.add(new URL(response.url()).pathname); });
      await page.route('**/*', route => {
        const url = route.request().url();
        if (url.startsWith(origin + '/') && /\.(png|jpe?g|webp|gif|svg)(\?|$)/i.test(url)) { localImages.push(url); return route.fulfill({ status: 404, body: '' }); }
        if (url.startsWith(origin) || url.startsWith(assets.origin + '/')) return route.continue();
        return route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
      });
      await page.goto(origin + '/shiritori.html');
      await page.waitForFunction(() => ST.wlLoaded);
      await page.locator('#titleImg').evaluate(image => image.decode());
      await page.locator('#noticeStart').click();
      await page.evaluate(() => { ST.voice = false; ST.skipLinkAnimation = true; ST.level = 5; });
      await page.locator('#titleScreen').click();
      await page.locator('#titleScreen').waitFor({ state: 'detached' });
      if(await page.locator('#playerSetup').isVisible())await page.locator('#playerSetupForm button[type="submit"]').click();
      await page.locator('#tabKbd').click();
      for (let turn = 0; turn < 3; turn++) {
        const reading = await page.evaluate(turn => {
          if (turn === 0) return 'りんご';
          return getPool().find(r => r.reading.startsWith(ST.tail) && !ST.used.has(r.reading) && !isEndWord(r.reading) && r.imagequeries.some(q => q.asset && q.mode !== 'none'))?.reading;
        }, turn);
        assert(reading, 'A valid next player word exists');
        await page.locator('#kbdInput').fill(reading);
        await page.locator('#kbdInput').press('Enter');
        await page.waitForFunction(count => !ST.cpuBusy && ST.history.length >= count, (turn + 1) * 2, { timeout: 60000 });
        assert.equal(await page.evaluate(() => ST.gameOver), false);
        const sequence = await page.evaluate(() => ST.history.map(e => ({ speaker: e.speaker, reading: e.reading })));
        assert.equal(sequence[turn * 2].reading, reading);
        assert.equal(sequence[turn * 2 + 1].speaker, 'CPU');
      }
      // Read a fixed meaning with a known image after three genuine CPU turns.
      await page.evaluate(() => showDetail('りんご', lookupRow('りんご')));
      if (width <= 768) await page.locator('#mobTabRight').click();
      await page.locator('#detImgBox .img-main').evaluate(image => image.decode());
      assert((await page.locator('#detImgBox .img-main').getAttribute('src')).startsWith(assets.origin + '/'));
      assert((await page.locator('#detContent').innerText()).includes(await page.evaluate(() => lookupRow('りんご').words[0])));
      await page.screenshot({ path: path.join(out, name + '-game.png'), fullPage: true });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      const history = await page.evaluate(() => ST.history.map(e => e.reading));
      if(await page.locator('#gameMenu summary').count())await page.locator('#gameMenu summary').click();await page.locator('#btnReset').click();
      assert.equal(await page.evaluate(() => ST.history.length), 0);
      await page.goto(origin + '/shiritori-image-review.html');
      await page.locator('#message').filter({ hasText: '準備できました' }).waitFor();
      await page.locator('#search').fill('りんご');
      await page.locator('#picture').evaluate(image => image.decode());
      assert((await page.locator('#picture').getAttribute('src')).startsWith(assets.origin + '/'));
      await page.locator('#checkImage').selectOption('ok');
      await page.screenshot({ path: path.join(out, name + '-review.png'), fullPage: true });
      assert.deepEqual(errors, []);
      results.push({ viewport: name, history, deliveredImages: delivered.size, errors });
      await page.close();
    }
    assert.deepEqual(localImages, [], 'No local/GitHub image fallback was requested');
    const result = { passed: true, appOrigin: origin, imageOrigin: assets.origin, localImages, results };
    fs.writeFileSync(path.join(out, process.env.QA_APP_ORIGIN ? 'live-results.json' : 'results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
