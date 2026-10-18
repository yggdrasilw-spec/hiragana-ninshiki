"""ETL processed PNGs -> 72-class katakana model. TensorFlow is imported on demand.

Images and models stay in the user's dataset/output directory, outside this repo.
The notebook embeds this file so that it works as a single uploaded artifact.
"""
from pathlib import Path, PurePosixPath
import csv
import hashlib
import json
import math
import random
import os
import shutil
import tempfile
import time
import unicodedata
import zipfile
from contextlib import ExitStack

import numpy as np
from PIL import Image, ImageDraw, ImageOps

VERSION = "katakana-marks-v2-close-spacing"
BASE_LABELS = list("ヲアイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワン")
VOICED = dict(zip("カキクケコサシスセソタチツテトハヒフヘホウ", "ガギグゲゴザジズゼゾダヂヅデドバビブベボヴ"))
SEMIVOICED = dict(zip("ハヒフヘホ", "パピプペポ"))
LABELS = BASE_LABELS + list(VOICED.values()) + list(SEMIVOICED.values())
SIZE = 64


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


class _ZipSet:
    """Expose several independent Drive download ZIPs as one read-only archive."""
    def __init__(self, paths):
        self.paths = paths

    def __enter__(self):
        self.stack = ExitStack()
        self.infos, self.owners = [], {}
        try:
            for index, path in enumerate(self.paths):
                bundle = self.stack.enter_context(zipfile.ZipFile(path))
                for info in bundle.infolist():
                    self.infos.append(info)
                    self.owners[id(info)] = (index, bundle)
        except BaseException:
            self.stack.close()
            raise
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def infolist(self):
        return self.infos

    def origin(self, info):
        return self.owners[id(info)][0]

    def open(self, info):
        return self.owners[id(info)][1].open(info)


def extract_dataset_zip(zip_path, local_dir, reserve_bytes=8 * 1024**3, progress=True,
                        labels=None, require_all=True):
    """Extract class PNGs from one or several local ZIPs, preserving class folders.

    The archive is read locally; no per-image Drive operations are involved.
    Source ZIP hash isolates different datasets and permits interrupted resumes.
    """
    allowed = BASE_LABELS if labels is None else list(labels)
    paths = [zip_path] if isinstance(zip_path, (str, Path)) else list(zip_path)
    archives = sorted({Path(path).resolve() for path in paths})
    if not archives:
        raise FileNotFoundError("ZIPをすべてColabのファイル欄へアップロードしてください")
    hashes = []
    for archive in archives:
        if not archive.is_file():
            raise FileNotFoundError(f"ZIPをColabのファイル欄へアップロードしてください: {archive}")
        if progress:
            print(f"ZIPを確認しています: {archive.name} ({archive.stat().st_size/1024**2:.1f} MiB)", flush=True)
        sha = hashlib.sha256()
        with archive.open("rb") as stream:
            for block in iter(lambda: stream.read(4 * 1024**2), b""):
                sha.update(block)
        hashes.append(sha.hexdigest())
    archive_hash = hashes[0] if len(hashes) == 1 else digest(sorted(hashes))
    local = (Path(local_dir) / archive_hash[:16]).resolve()
    local.mkdir(parents=True, exist_ok=True)
    entries, roots, targets = [], set(), set()
    with _ZipSet(archives) as bundle:
        for info in bundle.infolist():
            name = info.filename.replace("\\", "/")
            if not info.flag_bits & 0x800:
                try:
                    decoded = name.encode("cp437").decode("cp932")
                    if any(unicodedata.normalize("NFKC", part) in allowed for part in decoded.split("/")):
                        name = decoded
                except (UnicodeError, LookupError):
                    pass
            parts = PurePosixPath(name).parts
            if name.startswith("/") or ".." in parts or any(":" in p for p in parts):
                raise ValueError(f"Invalid ZIP path: {name}")
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError(f"ZIP symlink is not supported: {name}")
            if "__MACOSX" in parts or info.is_dir() or len(parts) < 2 or not name.lower().endswith(".png"):
                continue
            if unicodedata.normalize("NFKC", parts[-2]) not in allowed:
                continue
            roots.add((bundle.origin(info), parts[:-2]))
            relative = Path(parts[-2]) / (Path(parts[-1]).stem + ".png")
            if relative.as_posix() in targets:
                raise ValueError(f"Duplicate image in ZIP: {relative}")
            targets.add(relative.as_posix())
            entries.append((info, relative))
        if not entries:
            raise ValueError("ZIP内に『ｶ/画像.png』または『カ/画像.png』形式の画像がありません")
        if any(sum(origin == i for origin, _ in roots) > 1 for i in range(len(archives))):
            raise ValueError("ZIP内に複数のデータセットがあります。１つの画像フォルダだけをZIPにしてください")
        present = {unicodedata.normalize("NFKC", p.parent.name) for _, p in entries}
        missing = set(allowed) - present
        if missing and require_all:
            raise ValueError(f"ZIP全体で不足する文字: {sorted(missing)}。分割されたZIPをすべてアップロードしてください")
        required = sum(info.file_size for info, relative in entries if not (local / relative).is_file()
                       or (local / relative).stat().st_size != info.file_size)
        if shutil.disk_usage(local).free < required + reserve_bytes:
            raise OSError("Colabの空き容量が不足しています（展開画像と学習キャッシュ用の領域が必要です）")
        started, reused = time.monotonic(), 0
        if progress:
            print(f"ローカル展開: {len(entries):,}枚 / {sum(i.file_size for i, _ in entries)/1024**2:.1f} MiB", flush=True)
        for done, (info, relative) in enumerate(entries, 1):
            target = local / relative
            if target.is_symlink() or target.parent.is_symlink():
                raise ValueError(f"Unexpected linked destination: {target}")
            if target.is_file() and target.stat().st_size == info.file_size:
                reused += 1
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.with_suffix(".png.part")
                if temp.is_symlink():
                    raise ValueError(f"Unexpected temporary symlink: {temp}")
                with bundle.open(info) as src, temp.open("wb") as dst:
                    shutil.copyfileobj(src, dst)
                if temp.stat().st_size != info.file_size:
                    raise OSError(f"Incomplete ZIP extraction: {relative}")
                temp.replace(target)
            if progress and (done % 1000 == 0 or done == len(entries)):
                elapsed = time.monotonic() - started
                print(f"展開 {done:,}/{len(entries):,}枚 / 経過 {elapsed:.1f}秒 / 再利用 {reused:,}枚", flush=True)
    save_json(local / ".zip-complete.json", {"sha256": archive_hash, "files": len(entries)})
    return str(local)


def stage_dataset(source_dir, local_dir, reserve_bytes=8 * 1024**3, progress=True):
    """Copy PNGs once to Colab disk, then read only local images during processing.

    Atomic per-file replacement plus preserved source mtime/size allow restart of
    interrupted copies. This is a transfer check, not a substitute for inventory's
    decoded-pixel hash. A dedicated destination is bound to one source directory.
    """
    source, local = Path(source_dir).resolve(), Path(local_dir).resolve()
    if not source.is_dir():
        raise FileNotFoundError(source)
    if source == local or source in local.parents or local in source.parents:
        raise ValueError("Copy source and destination must be separate directories")
    local.mkdir(parents=True, exist_ok=True)
    marker = local / ".source.json"
    identity = {"source": str(source)}
    if marker.exists():
        if json.loads(marker.read_text(encoding="utf-8")) != identity:
            raise ValueError("Local directory belongs to a different source")
    elif any(local.iterdir()):
        raise ValueError("Choose a new empty staging directory")
    save_json(marker, identity)
    started = time.monotonic()
    if progress:
        print("DriveのPNG一覧を取得しています…", flush=True)
    files = []
    for folder in sorted(source.iterdir()):
        if folder.is_dir() and unicodedata.normalize("NFKC", folder.name) in BASE_LABELS:
            for path in sorted(folder.glob("*.png")):
                if path.is_symlink() or source not in path.resolve().parents:
                    raise ValueError(f"Unexpected linked source: {path}")
                stat = path.stat()
                files.append((path, path.relative_to(source), stat.st_size, stat.st_mtime_ns))
    if not files:
        raise ValueError("No base-class PNGs found")
    expected = {relative.as_posix() for _, relative, _, _ in files}
    stale = [p for p in local.glob("*/*.png") if p.relative_to(local).as_posix() not in expected]
    if stale:
        raise ValueError("Source file list changed; use a new staging directory")
    # Check available space before transfer, including room for the image cache.
    remaining_bytes = sum(size for _, relative, size, mtime in files
                          if not (local / relative).is_file()
                          or (local / relative).stat().st_size != size
                          or (local / relative).stat().st_mtime_ns != mtime)
    free = shutil.disk_usage(local).free
    if free < remaining_bytes + reserve_bytes:
        raise OSError(f"Insufficient local disk: need {remaining_bytes + reserve_bytes:,} bytes, free {free:,}")
    copied, reused = 0, 0
    if progress:
        print(f"コピー対象 {len(files):,}枚 / 合計 {sum(f[2] for f in files)/1024**2:.1f} MiB", flush=True)
    for done, (path, relative, size, mtime) in enumerate(files, 1):
        target = local / relative
        if target.is_symlink() or (target.parent.exists() and target.parent.is_symlink()):
            raise ValueError(f"Unexpected linked destination: {target}")
        if target.is_file() and target.stat().st_size == size and target.stat().st_mtime_ns == mtime:
            reused += 1
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_suffix(".png.part")
            if temp.is_symlink():
                raise ValueError(f"Unexpected linked temporary file: {temp}")
            shutil.copyfile(path, temp)
            if temp.stat().st_size != size or path.stat().st_mtime_ns != mtime:
                raise OSError(f"Source changed during copy: {path}")
            os.utime(temp, ns=(mtime, mtime))
            temp.replace(target)
            copied += 1
        if progress and (done % 250 == 0 or done == len(files)):
            elapsed = time.monotonic() - started
            rate = done / max(elapsed, .001)
            print(f"{done:,}/{len(files):,}枚 | 新規 {copied:,} / 再利用 {reused:,} | "
                  f"経過 {elapsed/60:.1f}分 / 残り約 {(len(files)-done)/rate/60:.1f}分", flush=True)
    save_json(local / ".transfer.json", {"files": len(files), "copied": copied, "reused": reused,
                                        "seconds": time.monotonic()-started})
    return str(local)


def ink_image(path, polarity="auto"):
    """Return white ink on black; flatten transparent backgrounds onto white."""
    with Image.open(path) as opened:
        rgba = opened.convert("RGBA")
        image = Image.alpha_composite(Image.new("RGBA", rgba.size, "white"), rgba).convert("L")
    arr = np.asarray(image)
    border = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]])
    if polarity not in ("auto", "white_on_black", "black_on_white"):
        raise ValueError("Unknown polarity")
    if polarity == "black_on_white" or (polarity == "auto" and np.median(border) > 127):
        image = ImageOps.invert(image)
    if not image.point(lambda p: 255 if p > 10 else 0).getbbox():
        raise ValueError(f"Blank image: {path}")
    return image


def tight(image):
    box = image.point(lambda p: 255 if p > 10 else 0).getbbox()
    if box is None:
        raise ValueError("No ink")
    return image.crop(box)


def normalize(image):
    """Browser contract: black background, white ink, bbox fit 85%, centered."""
    cropped = tight(image)
    scale = SIZE * .85 / max(cropped.size)
    # JS Math.round rather than Python banker's rounding.
    width, height = [max(1, math.floor(x * scale + .5)) for x in cropped.size]
    result = Image.new("L", (SIZE, SIZE))
    result.paste(cropped.resize((width, height), Image.Resampling.LANCZOS),
                 ((SIZE - width) // 2, (SIZE - height) // 2))
    return result


def draw_mark(kind, rng):
    """Procedural, jittered pen paths; no font or external image required."""
    scale = 4
    image = Image.new("L", (40 * scale, 40 * scale))
    draw = ImageDraw.Draw(image)
    width = rng.uniform(2.6, 4.8)
    if kind == "dakuten":
        for x in (9, 24):
            x += rng.uniform(-2, 2)
            y = rng.uniform(8, 12)
            dx, dy = rng.uniform(7, 13), rng.uniform(9, 16)
            pts = [(x, y), (x + dx * .45 + rng.uniform(-1, 1), y + dy * .5), (x + dx, y + dy)]
            pts = [(round(a * scale), round(b * scale)) for a, b in pts]
            w = round(width * scale)
            draw.line(pts, fill=255, width=w, joint="curve")
            for a, b in (pts[0], pts[-1]):
                draw.ellipse((a-w/2, b-w/2, a+w/2, b+w/2), fill=255)
    elif kind == "handakuten":
        rx, ry = rng.uniform(9, 13), rng.uniform(9, 13)
        phase = rng.uniform(0, 2 * math.pi)
        pts = []
        for i in range(65):
            angle = 2 * math.pi * i / 64
            wobble = 1 + .045 * math.sin(3 * angle + phase)
            pts.append(((20 + rx * math.cos(angle) * wobble) * scale,
                        (20 + ry * math.sin(angle) * wobble) * scale))
        draw.line(pts, fill=255, width=round(width * scale), joint="curve")
    else:
        raise ValueError(kind)
    image = image.rotate(rng.uniform(-18, 18), resample=Image.Resampling.BICUBIC)
    return tight(image).resize((28, 28), Image.Resampling.LANCZOS)


def dilate_ink(mask, radius):
    """Square dilation in O(pixels), without a SciPy/Colab dependency."""
    padded = np.pad(mask.astype(np.int32), radius)
    sums = np.pad(padded, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    size = 2 * radius + 1
    return (sums[size:, size:] - sums[:-size, size:]
            - sums[size:, :-size] + sums[:-size, :-size]) > 0


def place_mark(canvas, mark, bounds, rng):
    """Choose by actual ink distance, allowing overlapping empty bounding boxes.

    80% use a 3..6 pixel gap, 20% 7..11, on the 144px working canvas.
    Gap is Chebyshev distance between ink pixels, before final normalization.
    """
    x, y, bw, bh = bounds
    mw, mh = mark.size
    width, height = canvas.size
    gap = rng.randint(3, 6) if rng.random() < .8 else rng.randint(7, 11)
    ink = np.asarray(canvas) > 10
    mark_ink = np.asarray(mark) > 10
    forbidden = dilate_ink(ink, gap - 1)
    nearby = dilate_ink(ink, gap + 1)
    # Keep marks in the upper-right neighbourhood; let them enter the empty
    # space beside slanted/curved strokes instead of requiring an empty box.
    positions = [(mx, my)
                 for my in range(max(2, y - mh - 12), min(height - 2 - mh, y + bh // 3) + 1)
                 for mx in range(max(2, x + bw - mw - 16), min(width - 2 - mw, x + bw + 12) + 1)]
    rng.shuffle(positions)
    for mx, my in positions:
        region = np.s_[my:my + mh, mx:mx + mw]
        if not np.any(forbidden[region] & mark_ink) and np.any(nearby[region] & mark_ink):
            return mx, my, gap
    raise ValueError("Cannot place mark near upper-right ink without contact")


def compose(image, kind=None, seed=0, layout="natural", mark_path=None):
    """Place mark by the upper right of base ink; normalize the *whole* character.

    Alternate layouts also apply to clean letters to reduce a base-size shortcut.
    A hand-drawn donor (if provided) replaces the procedural mark.
    """
    rng = random.Random(seed)
    base = tight(image)
    canvas = Image.new("L", (144, 144))
    target = rng.randint(81, 88) if layout == "natural" else rng.randint(70, 82)
    scale = target / max(base.size)
    bw, bh = [max(1, round(d * scale)) for d in base.size]
    # Reserve enough height for even a wide top stroke (e.g. コ) plus the mark.
    x, y = rng.randint(8, 14), rng.randint(44, 46)
    canvas.paste(base.resize((bw, bh), Image.Resampling.LANCZOS), (x, y))
    if kind:
        mark = tight(ink_image(mark_path)) if mark_path else draw_mark(kind, rng)
        mw = rng.randint(18, 26)
        mh = max(8, round(mark.height * mw / mark.width))
        mh = min(mh, 28)
        mark = mark.resize((mw, mh), Image.Resampling.LANCZOS)
        mx, my, _ = place_mark(canvas, mark, (x, y, bw, bh), rng)
        # Empty corners of the mark's rectangle must not erase base strokes.
        region = np.asarray(canvas.crop((mx, my, mx + mw, my + mh)))
        canvas.paste(Image.fromarray(np.maximum(region, np.asarray(mark))), (mx, my))
    return normalize(canvas)


def inventory(dataset_dir, groups_csv=None, seed=20261016, polarity="auto", confirm_originals=False, progress=False):
    """Group original and augmented siblings before splitting, never after synthesis.

    CSV columns: path,group. path is relative to dataset_dir, group is writer ID
    (preferred) or original-record ID. A missing CSV only deduplicates exact pixels;
    transformed siblings cannot be inferred reliably from processed PNGs.
    """
    root = Path(dataset_dir)
    groups = None
    if groups_csv:
        groups = {}
        with open(groups_csv, encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                key = row["path"].replace("\\", "/")
                if key in groups or not row["group"].strip():
                    raise ValueError(f"Invalid/duplicate group row: {key}")
                groups[key] = row["group"].strip()
    dirs = {}
    for folder in root.iterdir():
        if folder.is_dir():
            name = unicodedata.normalize("NFKC", folder.name)
            if name in BASE_LABELS:
                if name in dirs:
                    raise ValueError(f"Duplicate class directories: {name}")
                dirs[name] = folder
    missing = set(BASE_LABELS) - dirs.keys()
    if missing:
        raise ValueError(f"Missing base classes: {sorted(missing)}")
    if progress:
        print("PNGのファイル一覧を取得しています（Driveではこの処理にも時間がかかります）", flush=True)
    files = {char: sorted(dirs[char].glob("*.png")) for char in BASE_LABELS}
    total = sum(len(paths) for paths in files.values())
    started, done = time.monotonic(), 0
    if progress:
        print(f"監査開始: {total:,}枚。GPUは使わず、画像を１枚ずつ読み込みます。", flush=True)
    rows, hashes, duplicates = [], {}, 0
    for char in BASE_LABELS:
        if progress:
            print(f"{char}: {len(files[char]):,}枚 / 全体 {done:,}/{total:,}", flush=True)
        for path in files[char]:
            relative = path.relative_to(root).as_posix()
            image = ink_image(path, polarity)
            h = hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()
            done += 1
            if progress and (done % 250 == 0 or done == total):
                elapsed = time.monotonic() - started
                rate = done / max(elapsed, .001)
                remaining = (total - done) / rate
                print(f"  {done:,}/{total:,} ({done/total:.1%}) | "
                      f"経過 {elapsed/60:.1f}分 | {rate:.1f}枚/秒 | 残り約 {remaining/60:.1f}分", flush=True)
            if groups is not None and relative not in groups:
                raise ValueError(f"Missing group ID: {relative}")
            group = groups[relative] if groups is not None else h
            if h in hashes:
                previous = hashes[h]
                if previous[0] != char or previous[1] != group:
                    raise ValueError(f"Conflicting duplicate image/group: {relative}")
                duplicates += 1
                continue
            hashes[h] = (char, group)
            # Whole writer groups remain together across character classes.
            value = int(hashlib.sha256(f"{seed}:{group}".encode()).hexdigest()[:8], 16) / 2**32
            split = "train" if value < .8 else "val" if value < .9 else "test"
            rows.append(dict(path=relative, base=char, group=group, split=split, sha256=h))
    for char in BASE_LABELS:
        for split in ("train", "val", "test"):
            if not any(r["base"] == char and r["split"] == split for r in rows):
                raise ValueError(f"No {split} source for {char}; more independent groups needed")
    grouping = "provided" if groups is not None else "confirmed_original_records" if confirm_originals else "exact_pixels_only"
    return rows, {"grouping": grouping,
                  "removed_exact_duplicates": duplicates, "source_count": len(rows)}


def make_examples(sources, variants=2, seed=20261016):
    if variants < 1:
        raise ValueError("variants must be >= 1")
    examples = []
    for source in sources:
        targets = [(source["base"], None)]
        if source["base"] in VOICED:
            targets.append((VOICED[source["base"]], "dakuten"))
        if source["base"] in SEMIVOICED:
            targets.append((SEMIVOICED[source["base"]], "handakuten"))
        for label, kind in targets:
            for variant in range(variants):
                row_seed = int(digest([seed, source["sha256"], label, variant])[:12], 16)
                examples.append({**source, "label": label, "kind": kind, "seed": row_seed,
                                 "layout": "natural" if variant % 2 == 0 else "compact"})
    return examples


def render_example(row, root, polarity="auto", mark_bank=None):
    donor = None
    if row["kind"] and mark_bank:
        donors = sorted((Path(mark_bank) / row["kind"] / row["split"]).glob("*.png"))
        if not donors:
            raise ValueError(f"No independent {row['split']} mark donors for {row['kind']}")
        donor = donors[row["seed"] % len(donors)]
    return compose(ink_image(Path(root) / row["path"], polarity), row["kind"],
                   row["seed"], row["layout"], donor)


def preview(examples, root, output, polarity="auto", mark_bank=None):
    """Rows are base / voiced / semi-voiced. Labels are in an adjacent JSON index."""
    selected = []
    for base in VOICED:
        labels = [base, VOICED[base], SEMIVOICED.get(base)]
        selected.append([next((r for r in examples if r["label"] == label), None) for label in labels])
    cell = 144
    sheet = Image.new("RGB", (len(selected) * cell, 3 * cell), "#d8d8d8")
    index = []
    for col, triplet in enumerate(selected):
        for row_no, row in enumerate(triplet):
            if row:
                im = render_example(row, root, polarity, mark_bank).resize((128, 128))
                sheet.paste(im.convert("RGB"), (col * cell + 8, row_no * cell + 8))
                index.append({"column": col, "row": row_no, "label": row["label"], "source": row["path"]})
    sheet.save(output)
    save_json(Path(output).with_suffix(".json"), index)
    return sheet


def dataset(examples, root, split, batch=128, polarity="auto", mark_bank=None, cache_file=None):
    import tensorflow as tf
    rows = [row for row in examples if row["split"] == split]
    if split == "train":
        # Avoid batches dominated by one class even when the local shuffle buffer
        # is smaller than a class. This order is also what gets disk-cached.
        random.Random(20261016).shuffle(rows)

    def generate():
        for row in rows:
            image = render_example(row, root, polarity, mark_bank)
            yield np.asarray(image, dtype=np.float32)[..., None] / 255., np.int32(LABELS.index(row["label"]))

    ds = tf.data.Dataset.from_generator(generate, output_signature=(
        tf.TensorSpec((SIZE, SIZE, 1), tf.float32), tf.TensorSpec((), tf.int32)))
    ds = ds.apply(tf.data.experimental.assert_cardinality(len(rows)))
    if cache_file:
        # Store the first generated pass on local Colab disk, not Google Drive.
        ds = ds.cache(str(cache_file))
    if split == "train":
        ds = ds.shuffle(min(4096, len(rows)), seed=20261016, reshuffle_each_iteration=True)
    return ds.batch(batch).prefetch(1)


def build_model(baseline=None):
    import tensorflow as tf
    layers = tf.keras.layers
    model = tf.keras.Sequential([
        layers.Input((64, 64, 1)),
        layers.Conv2D(32, 3, activation="relu"), layers.MaxPooling2D(), layers.Dropout(.25),
        layers.Conv2D(32, 3, activation="relu"), layers.MaxPooling2D(), layers.Dropout(.25),
        layers.Conv2D(32, 3, activation="relu"), layers.MaxPooling2D(), layers.Dropout(.25),
        layers.Flatten(), layers.Dense(512, activation="relu"), layers.Dropout(.25),
        layers.Dense(len(LABELS), activation="softmax")])
    if baseline:
        old = tf.keras.models.load_model(baseline, compile=False)
        if old.input_shape[1:] != (64, 64, 1) or old.output_shape[-1] != 46:
            raise ValueError("Baseline must be the original 64x64 / 46-class model")
        old_layers = [layer for layer in old.layers if layer.weights]
        new_layers = [layer for layer in model.layers if layer.weights]
        if len(old_layers) != len(new_layers):
            raise ValueError("Baseline architecture mismatch")
        for a, b in zip(old_layers[:-1], new_layers[:-1]):
            b.set_weights(a.get_weights())
        kernel, bias = new_layers[-1].get_weights()
        old_kernel, old_bias = old_layers[-1].get_weights()
        kernel[:, :46], bias[:46] = old_kernel, old_bias
        new_layers[-1].set_weights([kernel, bias])
    model.compile(optimizer=tf.keras.optimizers.Adam(2e-4),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train(examples, dataset_dir, output_dir, metadata, epochs=100, batch=128,
          baseline=None, polarity="auto", mark_bank=None, allow_unverified_groups=False):
    import tensorflow as tf
    if metadata["grouping"] not in ("provided", "confirmed_original_records") and not allow_unverified_groups:
        raise ValueError("Original/writer groups are unknown. Preview works, but training is stopped. "
                         "Provide groups.csv, or explicitly allow a diagnostic run with possible leakage.")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    contract = dict(version=VERSION, labels=LABELS, examples_digest=digest(examples),
                    metadata=metadata, polarity=polarity, batch=batch,
                    mark_bank=str(mark_bank), seed=20261016)
    # Donor content changes also invalidate a resumed experiment.
    if mark_bank:
        contract["donors"] = {p.relative_to(mark_bank).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted(Path(mark_bank).rglob("*.png"))}
        donor_splits = {}
        for relative, sha in contract["donors"].items():
            parts = Path(relative).parts
            if len(parts) != 3 or parts[0] not in ("dakuten", "handakuten") or parts[1] not in ("train", "val", "test"):
                raise ValueError(f"Unexpected mark-bank path: {relative}")
            donor_splits.setdefault(sha, set()).add(parts[1])
        if any(len(splits) > 1 for splits in donor_splits.values()):
            raise ValueError("Identical mark donor appears in multiple splits")
    if baseline:
        contract["baseline_sha256"] = hashlib.sha256(Path(baseline).read_bytes()).hexdigest()
    config_path = out / "experiment.json"
    if config_path.exists() and json.loads(config_path.read_text(encoding="utf-8")) != contract:
        raise ValueError("Output directory belongs to a different experiment; choose a new directory")
    save_json(config_path, contract)
    save_json(out / "labels.json", LABELS)
    (out / "katakana_labels_full.txt").write_text("".join(LABELS), encoding="utf-8")
    (out / "labels.js").write_text("const LABELS_KATAKANA = " + json.dumps(LABELS, ensure_ascii=False) + ";\n", encoding="utf-8")
    save_json(out / "examples.json", examples)
    state_path = out / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {
        "epoch": 0, "best": -1., "wait": 0}
    last = out / f"epoch-{state['epoch']:04d}.keras"
    model = tf.keras.models.load_model(last) if state["epoch"] else build_model(baseline)
    cache_dir = Path(tempfile.gettempdir()) / "katakana-cache" / digest(contract)
    cache_dir.mkdir(parents=True, exist_ok=True)
    train_ds = dataset(examples, dataset_dir, "train", batch, polarity, mark_bank, cache_dir / "train")
    val_ds = dataset(examples, dataset_dir, "val", batch, polarity, mark_bank, cache_dir / "val")

    class SaveEpoch(tf.keras.callbacks.Callback):
        def on_epoch_end(self, epoch, logs=None):
            score = float(logs["val_accuracy"])
            if not math.isfinite(score):
                raise ValueError("Non-finite validation accuracy")
            improved = score > state["best"]
            new_state = {"epoch": epoch+1, "best": max(state["best"], score),
                         "wait": 0 if improved else state["wait"]+1}
            # Immutable epoch file; state commits only after complete model save.
            current = out / f"epoch-{epoch+1:04d}.keras"
            self.model.save(current)
            if improved:
                new_state["best_epoch"] = epoch+1
            else:
                new_state["best_epoch"] = state["best_epoch"]
            save_json(state_path, new_state)
            state.update(new_state)
            if state["wait"] >= 20:
                self.model.stop_training = True

    if state["wait"] < 20 and state["epoch"] < epochs:
        model.fit(train_ds, validation_data=val_ds, epochs=epochs, initial_epoch=state["epoch"],
                  callbacks=[SaveEpoch(), tf.keras.callbacks.CSVLogger(str(out / "history.csv"), append=True)])
    if "best_epoch" not in state:
        raise ValueError("No completed epoch")
    best_path = out / f"epoch-{state['best_epoch']:04d}.keras"
    print("Best checkpoint:", best_path)
    return tf.keras.models.load_model(best_path)


def evaluate(model, examples, root, output, polarity="auto", mark_bank=None, baseline=None):
    """Held-out *synthetic* test. Never describe it as real voiced-handwriting accuracy."""
    ds = dataset(examples, root, "test", polarity=polarity, mark_bank=mark_bank)
    true, probs, old_probs = [], [], []
    for images, labels in ds:
        true.extend(labels.numpy().tolist())
        probs.extend(model(images, training=False).numpy())
        if baseline is not None:
            old_probs.extend(baseline(images, training=False).numpy())
    probs, true = np.asarray(probs), np.asarray(true)
    ids = probs.argmax(axis=1)
    top5 = np.argsort(probs, axis=1)[:, -5:]
    cm = np.zeros((len(LABELS), len(LABELS)), dtype=int)
    np.add.at(cm, (true, ids), 1)
    result = {"evaluation": "held-out sources with synthetic marks; not real handwriting accuracy",
              "top1": float(np.mean(ids == true)), "top5": float(np.mean((top5 == true[:, None]).any(axis=1))),
              "characters": {}, "confusion": cm.tolist()}
    for i, char in enumerate(LABELS):
        mask = true == i
        result["characters"][char] = {"count": int(mask.sum()), "top1": float(np.mean(ids[mask] == i))}
    if baseline is not None:
        mask = true < 46
        result["clean_same_inputs"] = {
            "baseline": float(np.mean(np.asarray(old_probs).argmax(axis=1)[mask] == true[mask])),
            "new": float(np.mean(ids[mask] == true[mask]))}
    save_json(output, result)
    return result
