const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');

const defaultPath = path.join(__dirname, '../assets/shiritori/manifest.json');

function readManifest(file = defaultPath) {
    const index = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (Array.isArray(index.assets)) return index;
    if (index.manifestVersion !== 2) throw new Error('Unsupported image manifest version');

    function readShards(kind) {
        const records = new Map();
        for (const name of index.shards[kind]) {
            const match = /^manifest-data\/(assets|prompts)-[0-9a-f]{2}-([0-9a-f]{64})\.json$/.exec(name);
            if (match?.[1] !== kind) throw new Error(`Invalid manifest shard: ${name}`);
            const data = fs.readFileSync(path.join(path.dirname(file), name));
            if (createHash('sha256').update(data).digest('hex') !== match[2]) {
                throw new Error(`Manifest shard checksum mismatch: ${name}`);
            }
            for (const [key, record] of Object.entries(JSON.parse(data))) {
                if (records.has(key)) throw new Error(`Duplicate manifest record: ${key}`);
                records.set(key, record);
            }
        }
        return records;
    }

    const records = readShards('assets');
    const prompts = readShards('prompts');
    const files = Object.entries(index.files);
    if (files.length !== records.size) throw new Error('Manifest index and asset shards disagree');
    const assets = files.map(([name, promptId]) => {
        const asset = records.get(name);
        if (!asset) throw new Error(`Missing image record: ${name}`);
        if (promptId !== null) {
            if (!prompts.has(promptId)) throw new Error(`Missing image prompt: ${promptId}`);
            asset.prompt = prompts.get(promptId);
        }
        return asset;
    });
    return {...index.metadata, assets};
}

module.exports = {readManifest};
