// Extract unchanged path strings; the resulting dataset remains CC BY-SA 3.0.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const source=process.argv[2];if(!source)throw Error('Usage: node scripts/build-kana-feedback-reference.cjs path/to/kana.json');
const bytes=fs.readFileSync(source),data=JSON.parse(bytes);
const chars=Array.from({length:86},(_,i)=>String.fromCharCode(0x3041+i));
const result={version:2,source:'KanjiVG',author:'Ulrich Apel',url:'https://kanjivg.tagaini.net/',license:'CC BY-SA 3.0',licenseUrl:'https://creativecommons.org/licenses/by-sa/3.0/',changes:'Selected all 86 hiragana U+3041-U+3096; SVG path strings unchanged. Sampled and scaled only for display/comparison.',inputSha256:crypto.createHash('sha256').update(bytes).digest('hex'),glyphs:{}};
for(const ch of chars){if(!data.glyphs[ch]?.paths?.length)throw Error('Missing '+ch);result.glyphs[ch]={paths:data.glyphs[ch].paths};}
fs.writeFileSync(path.resolve(__dirname,'../data/kana-feedback-reference.json'),JSON.stringify(result,null,2)+'\n');
console.log('Extracted '+chars.join(' ')+'; CC BY-SA 3.0');
