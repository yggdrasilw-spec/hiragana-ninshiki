// Count using the application's parser, including its homophone grouping/minimum level.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'shiritori.html'), 'utf8');
const source = html.slice(html.indexOf('function parseCSV('), html.indexOf('const ST ='));
const context = vm.createContext({ csv: fs.readFileSync(path.join(root, 'whitelist.csv'), 'utf8') });
vm.runInContext(source, context);
const readings = vm.runInContext('parseCSV(csv)', context);
const initials = 'あいうえおかがきぎくぐけげこごさざしじすずせぜそぞただちぢつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもやゆよらりるれろわをん';
const summary = [...initials].map(kana => {
  const words = readings.filter(r => r.reading.startsWith(kana));
  const safe = words.filter(r => !r.reading.endsWith('ん'));
  return { kana, total: words.length, easy: words.filter(r => r.level === 1).length, normal: words.filter(r => r.level <= 2).length, easySafe: safe.filter(r => r.level === 1).length, normalSafe: safe.filter(r => r.level <= 2).length };
});
console.log(JSON.stringify({ rows: context.csv.trim().split(/\r?\n/).length - 1, readings: readings.length, assets: readings.flatMap(r=>r.imagequeries).filter(q=>q.asset).length, summary }, null, 2));
