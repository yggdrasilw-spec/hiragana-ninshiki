const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = path.resolve(__dirname, '..');
const output = process.env.QA_OUTPUT || path.join(root, 'qa-output');
const imageCases = JSON.parse(fs.readFileSync(path.join(root, 'assets/shiritori/manifest.json'), 'utf8')).assets;
const server = http.createServer((req, res) => {
  const relative = decodeURIComponent(new URL(req.url, 'http://localhost').pathname).replace(/^\/+/, '');
  const file = path.resolve(root, relative || 'shiritori.html');
  if (!file.startsWith(root + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); res.end(); return; }
  const types = { '.html': 'text/html; charset=utf-8', '.csv': 'text/csv; charset=utf-8', '.txt': 'text/plain; charset=utf-8', '.png': 'image/png', '.json': 'application/json', '.wav': 'audio/wav' };
  res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
(async () => {
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true, channel: process.env.QA_BROWSER || 'chrome' });
  try {
    fs.mkdirSync(output, { recursive: true });
    for (const [name, viewport] of [['desktop', { width: 1280, height: 900 }], ['mobile', { width: 390, height: 844 }]]) {
      const page = await browser.newPage({ viewport });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      // Deterministic search failure, including offline operation. Local assets remain available.
      await page.route('**/*', route => route.request().url().startsWith(origin) ? route.continue() : route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }));
      await page.goto(origin + '/shiritori.html');
      await page.waitForFunction(() => ST.wlLoaded);
      await page.evaluate(() => { ST.voice = false; document.getElementById('titleScreen')?.remove(); switchIn('keyboard'); });
      if (name === 'mobile') await page.locator('#mobTabRight').click();
      for (const { reading, file: filename, word } of imageCases) {
        await page.evaluate(reading => showDetail(reading, lookupRow(reading)), reading);
        await page.waitForFunction(filename => {
          const image = document.querySelector('#detImgBox .img-main');
          return image?.src.endsWith(filename) && image.complete && image.naturalWidth > 0;
        }, filename);
        assert.match(await page.locator('#detImgBox .img-credit').innerText(), /AI生成イラスト/);
        assert.ok(await page.locator('#detImgBox .img-main').isVisible());
        assert.ok((await page.locator('#detContent').innerText()).includes(word));
        await page.screenshot({ path: path.join(output, `${name}-${path.parse(filename).name}.png`), fullPage: true });
      }
      // Meanings sharing one reading retain their own image and credit in the slideshow.
      await page.evaluate(() => showDetail('はし', {
        reading: 'はし', words: ['意味その一', '意味その二'], meanings: ['説明その一', '説明その二'],
        imagequeries: [
          { ja: '同じ検索語', asset: 'assets/shiritori/hakushu.png', mode: 'asset', credit: '画像その一' },
          { ja: '同じ検索語', asset: 'assets/shiritori/hayane.png', mode: 'asset', credit: '画像その二' }
        ]
      }));
      await page.waitForFunction(() => document.querySelector('#detImgBox .img-main')?.src.endsWith('hakushu.png'));
      await page.waitForFunction(() => document.querySelector('#detImgBox .img-main')?.src.endsWith('hayane.png'));
      assert.match(await page.locator('#detContent').innerText(), /意味その二/);
      assert.equal(await page.locator('#detImgBox .img-credit').innerText(), '画像その二');
      assert.deepEqual(errors, []);
      assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'No horizontal overflow');
      await page.close();
    }
    console.log(JSON.stringify({ passed: true, viewports: ['desktop', 'mobile'], assets: imageCases.map(a => a.file), output }));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; }).finally(() => server.close());
