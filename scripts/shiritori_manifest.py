"""Read and update the sharded shiritori image catalog."""

import argparse
from collections import defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import tempfile


MANIFEST = Path(__file__).resolve().parents[1] / "assets/shiritori/manifest.json"
SHARD = re.compile(r"manifest-data/(assets|prompts)-[0-9a-f]{2}-([0-9a-f]{64})\.json")


def digest(data):
    return sha256(data).hexdigest()


def json_line(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_object(items):
    lines = (f"  {json_line(key)}: {json_line(value)}" for key, value in items.items())
    return ("{\n" + ",\n".join(lines) + "\n}\n").encode("utf-8")


def read_manifest(path=MANIFEST, read_bytes=Path.read_bytes):
    path = Path(path)
    index = json.loads(read_bytes(path))
    if "assets" in index:  # Historical revisions and registration fixtures.
        return index
    if index.get("manifestVersion") != 2:
        raise ValueError("Unsupported image manifest version")

    def read_shards(kind):
        records = {}
        for name in index["shards"][kind]:
            match = SHARD.fullmatch(name)
            if not match or match[1] != kind:
                raise ValueError(f"Invalid manifest shard: {name}")
            data = read_bytes(path.parent / name)
            if digest(data) != match[2]:
                raise ValueError(f"Manifest shard checksum mismatch: {name}")
            shard = json.loads(data)
            if records.keys() & shard.keys():
                raise ValueError(f"Duplicate manifest record: {name}")
            records.update(shard)
        return records

    assets = read_shards("assets")
    prompts = read_shards("prompts")
    if assets.keys() != index["files"].keys():
        raise ValueError("Manifest index and asset shards disagree")
    for file, prompt_id in index["files"].items():
        if prompt_id is not None:
            assets[file]["prompt"] = prompts[prompt_id]
    return {**index["metadata"], "assets": [assets[file] for file in index["files"]]}


def atomic_write(path, data):
    if path.exists() and path.read_bytes() == data:
        return
    stream = tempfile.NamedTemporaryFile(dir=path.parent, delete=False)
    temporary = Path(stream.name)
    try:
        with stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_manifest(path, manifest):
    """Write the new shards first and publish the index last. Use one writer."""
    path = Path(path)
    files = {}
    assets = defaultdict(dict)
    prompts = defaultdict(dict)
    for asset in manifest["assets"]:
        file = asset["file"]
        if file in files:
            raise ValueError(f"Duplicate image filename: {file}")
        record = dict(asset)
        prompt_id = None
        if "prompt" in record:
            prompt = record.pop("prompt")
            prompt_id = digest(prompt.encode("utf-8"))
            prompts[prompt_id[:1]][prompt_id] = prompt
        files[file] = prompt_id
        bucket = int(digest(file.encode("utf-8"))[:2], 16) % 32
        assets[f"{bucket:02x}"][file] = record

    index = {
        "manifestVersion": 2,
        "metadata": {key: value for key, value in manifest.items() if key != "assets"},
        "shards": {},
    }
    shard_dir = path.parent / "manifest-data"
    shard_dir.mkdir(exist_ok=True)
    active = set()
    for kind, buckets in (("assets", assets), ("prompts", prompts)):
        names = index["shards"][kind] = []
        for bucket, records in sorted(buckets.items()):
            data = json_object(dict(sorted(records.items())))
            name = f"manifest-data/{kind}-{int(bucket, 16):02x}-{digest(data)}.json"
            atomic_write(path.parent / name, data)
            names.append(name)
            active.add(name)
    # Keep each filename on its own line for diffs and preserve catalog order.
    files_json = "\n  ".join(json_object(files).decode("utf-8").strip().splitlines())
    header = json.dumps(index, ensure_ascii=False, indent=2)
    atomic_write(path, (header[:-2] + ',\n  "files": ' + files_json + "\n}\n").encode("utf-8"))
    for shard in shard_dir.glob("*.json"):
        name = f"manifest-data/{shard.name}"
        if name not in active and SHARD.fullmatch(name):
            shard.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("migrate", "export"))
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", type=Path, help="Destination for a legacy JSON export")
    args = parser.parse_args()
    manifest = read_manifest(args.manifest)
    if args.command == "migrate":
        write_manifest(args.manifest, manifest)
    else:
        if not args.output or args.output.resolve() == args.manifest.resolve():
            parser.error("export requires a separate --output path")
        args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
