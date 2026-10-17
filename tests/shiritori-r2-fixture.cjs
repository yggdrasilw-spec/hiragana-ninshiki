// Deterministic offline suites mirror the trusted delivery origin from local fixtures.
// The separate shiritori-r2-browser suite always uses the real deployed Worker.
const path = require('node:path'), fs = require('node:fs');
const assets = require('../shiritori-assets.js');
module.exports = async function storedImageFixtures(page) {
  const root = process.env.REVIEW_ROOT || path.resolve(__dirname, '..');
  await page.route(assets.origin + '/**', async route => {
    const key = new URL(route.request().url()).pathname.slice(1);
    const file = assets.url(key) && path.join(root, key);
    if (!file || !fs.existsSync(file)) return route.fulfill({ status: 404, body: '' });
    await route.fulfill({ path: file, contentType: /\.webp$/i.test(key) ? 'image/webp' : /\.jpe?g$/i.test(key) ? 'image/jpeg' : 'image/png', headers: { 'Access-Control-Allow-Origin': '*' } });
  });
};
