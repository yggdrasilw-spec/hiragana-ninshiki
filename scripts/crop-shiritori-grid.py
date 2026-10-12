"""Fail-closed extraction of marked vocabulary sheets, without large margins.

The generator must draw uninterrupted magenta grid lines, including outer
borders. Remove only measured divider lines and their fringes. No equal-quarter
fallback, manual crop override, or output is allowed when validation fails.
"""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


class GridError(ValueError):
    pass


def marker_mask(rgb):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    return (r >= 190) & (b >= 190) & (g <= 110) & (abs(r - b) <= 70)


def divider_fringe_mask(rgb):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    return (r >= 220) & (b >= 220) & (r - g >= 8) & (b - g >= 8)


def line_bands(mask, axis, count, fringe=None, minimum_fringe_support=0):
    support = mask.mean(axis=axis)
    indices = np.flatnonzero(support >= 0.94)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    groups = [g for g in groups if len(g)]
    length = len(support)
    fringe_support = (fringe if fringe is not None else mask).mean(axis=axis)
    fringe_threshold = max(minimum_fringe_support, float(np.median(fringe_support)) + 0.003)
    if len(groups) != count + 1:
        raise GridError(f'Expected {count + 1} continuous grid lines; found {len(groups)}')
    bands = []
    for i, group in enumerate(groups):
        lo, hi = int(group[0]), int(group[-1]) + 1
        # Include antialiasing at the divider edges only, never trim the art.
        while lo > 0 and fringe_support[lo - 1] > fringe_threshold:
            lo -= 1
        while hi < length and fringe_support[hi] > fringe_threshold:
            hi += 1
        center = (lo + hi - 1) / 2
        expected = i * (length - 1) / count
        if abs(center - expected) > length * 0.025:
            raise GridError(f'Grid line {i} is displaced from the agreed layout')
        if hi - lo < 2 or hi - lo > length * 0.025:
            raise GridError(f'Grid line {i} has invalid thickness')
        bands.append([lo, hi])
    if bands[0][0] > 2 or bands[-1][1] < length - 2:
        raise GridError('Outer frame is missing or does not enclose the sheet')
    return bands


def refine_tinted_edges(rgb, bands, perpendicular, axis, include_core=False):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    tint = (r >= 245) & (b >= 245) & (g <= 240) & (abs(r - b) <= 3)
    if include_core:
        tint |= marker_mask(rgb)
    if axis == 0:
        for lo, hi in perpendicular:
            tint[lo:hi, :] = False
    else:
        for lo, hi in perpendicular:
            tint[:, lo:hi] = False
    present = tint.any(axis=axis)
    refined = []
    for lo, hi in bands:
        candidates = np.flatnonzero(present[max(0, lo - 4):min(len(present), hi + 4)]) + max(0, lo - 4)
        if len(candidates):
            lo, hi = min(lo, int(candidates[0])), max(hi, int(candidates[-1]) + 1)
        refined.append([lo, hi])
    return refined


def extract(image, columns=4, rows=4, method='magenta-grid-lines-only-v4'):
    image = image.convert('RGB')
    rgb = np.asarray(image)
    if min(image.size) < max(columns, rows) * 96:
        raise GridError('Source resolution is too small')
    mask = marker_mask(rgb)
    fringe = divider_fringe_mask(rgb)
    if method in ('magenta-grid-lines-only-v3', 'magenta-grid-lines-only-v4'):
        # Broad pastel/sepia pixels are artwork, not a divider fringe. Exclude
        # perpendicular core lines from fringe support so their constant ~3%
        # contribution cannot make isolated art pixels expand an entire band.
        r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
        tint = mask | ((r >= 190) & (b >= 190) & (abs(r - b) <= 20) & (r - g >= 8) & (b - g >= 8))
        vertical_fringe = tint.copy()
        horizontal_fringe = tint.copy()
        vertical_fringe[mask.mean(axis=1) >= 0.94, :] = False
        horizontal_fringe[:, mask.mean(axis=0) >= 0.94] = False
        xs = line_bands(mask, 0, columns, vertical_fringe, 0.20)
        ys = line_bands(mask, 1, rows, horizontal_fringe, 0.20)
    else:
        xs = line_bands(mask, 0, columns, fringe)
        ys = line_bands(mask, 1, rows, fringe)
    if method in ('magenta-grid-lines-only-v2', 'magenta-grid-lines-only-v3', 'magenta-grid-lines-only-v4'):
        xs = refine_tinted_edges(rgb, xs, ys, 0, include_core=method in ("magenta-grid-lines-only-v3", "magenta-grid-lines-only-v4"))
        ys = refine_tinted_edges(rgb, ys, xs, 1, include_core=method in ("magenta-grid-lines-only-v3", "magenta-grid-lines-only-v4"))
    if method == 'magenta-grid-lines-only-v4':
        # Refining one axis can reveal a sparse antialiased fringe on the other.
        # Iterate measured tint bounds to stability; never substitute a fixed crop.
        for _ in range(5):
            next_xs = refine_tinted_edges(rgb, xs, ys, 0, include_core=True)
            next_ys = refine_tinted_edges(rgb, ys, next_xs, 1, include_core=True)
            if next_xs == xs and next_ys == ys:
                break
            xs, ys = next_xs, next_ys
        else:
            raise GridError('Divider fringe measurements did not stabilize')
        for bands, length, count in ((xs, image.width, columns), (ys, image.height, rows)):
            for i, (lo, hi) in enumerate(bands):
                if hi - lo > length * 0.025 or abs((lo + hi - 1) / 2 - i * (length - 1) / count) > length * 0.025:
                    raise GridError('Refined divider exceeds agreed geometry')
    widths = [xs[i + 1][0] - xs[i][1] for i in range(columns)]
    heights = [ys[i + 1][0] - ys[i][1] for i in range(rows)]
    if max(widths) / min(widths) > 1.10 or max(heights) / min(heights) > 1.10:
        raise GridError('Cell dimensions are inconsistent')
    prepared = []
    for index in range(columns * rows):
        y, x = divmod(index, columns)
        box = [xs[x][1], ys[y][1], xs[x + 1][0], ys[y + 1][0]]
        tile = rgb[box[1]:box[3], box[0]:box[2]]
        if marker_mask(tile).any():
            raise GridError(f'Tile {index + 1}: divider color leaked inside the crop')
        # Edge occupancy is diagnostic only in v2: large blank margins are not required.
        ink = tile.min(axis=2) < 225
        h, w = ink.shape
        gx, gy = max(3, round(w * 0.05)), max(3, round(h * 0.05))
        guard = np.ones((h, w), dtype=bool)
        guard[gy:h - gy, gx:w - gx] = False
        edge_fraction = float(ink[guard].mean())
        if method == 'magenta-grid-white-guard-v1' and edge_fraction > 0.005:
            raise GridError(f'Tile {index + 1}: white safety margin failed ({edge_fraction:.4%})')
        content_fraction = float(ink.mean())
        if content_fraction < 0.01 or (method == 'magenta-grid-white-guard-v1' and content_fraction > 0.70):
            raise GridError(f'Tile {index + 1}: empty or overfilled cell')
        if method in ('magenta-grid-lines-only-v2', 'magenta-grid-lines-only-v3', 'magenta-grid-lines-only-v4'):
            # A divider fringe has nearly equal, almost-maximal R and B.
            # Pale blue/grey objects near an edge must not be mistaken for it.
            residue = (divider_fringe_mask(tile) & (tile[:, :, 0] >= 245)
                       & (tile[:, :, 2] >= 245)
                       & (tile[:, :, 1] <= 240)
                       & (abs(tile[:, :, 0].astype(int) - tile[:, :, 2].astype(int)) <= 3))
            if (residue[:2].any() or residue[-2:].any()
                    or residue[:, :2].any() or residue[:, -2:].any()):
                raise GridError(f'Tile {index + 1}: divider fringe remains at the crop edge')
        result = ImageOps.pad(image.crop(box), (256, 256),
                              method=Image.Resampling.LANCZOS, color='white')
        prepared.append((result, {'tileIndex': index + 1, 'cropBox': box,
                                  'edgeInkFraction': edge_fraction,
                                  'contentFraction': content_fraction}))
    return prepared, {'columnBands': xs, 'rowBands': ys}


def verify_report(report_path, source_path, output_directory):
    """Recompute geometry and every PNG before trusting registration evidence."""
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if (report.get('version') != 1 or report.get('passed') is not True
            or report.get('method') not in ('magenta-grid-white-guard-v1', 'magenta-grid-lines-only-v2', 'magenta-grid-lines-only-v3', 'magenta-grid-lines-only-v4')
            or report.get('columns') != 4 or report.get('rows') != 4):
        raise GridError('Unrecognized or failed extraction report')
    if hashlib.sha256(Path(source_path).read_bytes()).hexdigest() != report['sourceSha256']:
        raise GridError('Source sheet hash differs from extraction report')
    with Image.open(source_path) as source:
        if list(source.size) != report['sourceSize']:
            raise GridError('Source dimensions differ from report')
        prepared, geometry = extract(source, method=report['method'])
    if any(report.get(k) != v for k, v in geometry.items()) or len(report['tiles']) != 16:
        raise GridError('Recorded boundaries or tile count differ from measured grid')
    names = set()
    result = {}
    for entry, (image, checks) in zip(report['tiles'], prepared):
        name = entry['file']
        if not re.fullmatch(r'[A-Za-z0-9_-]+\.png', name) or name in names:
            raise GridError('Unsafe or duplicate tile name in report')
        names.add(name)
        if any(entry.get(k) != v for k, v in checks.items()):
            raise GridError('Crop box, order or safety checks differ from measured sheet')
        stream = io.BytesIO()
        image.save(stream, format='PNG', optimize=True)
        expected = hashlib.sha256(stream.getvalue()).hexdigest()
        if (entry['sha256'] != expected or hashlib.sha256(
                (Path(output_directory) / name).read_bytes()).hexdigest() != expected):
            raise GridError(f'Image does not reproduce from validated source: {name}')
        result[name] = entry
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('--columns', type=int, default=4)
    parser.add_argument('--rows', type=int, default=4)
    parser.add_argument('--method', choices=['magenta-grid-white-guard-v1', 'magenta-grid-lines-only-v2', 'magenta-grid-lines-only-v3', 'magenta-grid-lines-only-v4'], default='magenta-grid-lines-only-v4')
    parser.add_argument('--names', required=True)
    parser.add_argument('--output', type=Path, default=Path('assets/shiritori'))
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--verify-existing', action='store_true', help='Recompute and verify an existing report and all 16 PNGs without writing')
    args = parser.parse_args()
    names = [s.strip() for s in args.names.split(',')]
    if args.columns < 1 or args.rows < 1 or len(names) != args.columns * args.rows:
        parser.error('Supply exactly rows x columns names')
    if len(set(names)) != len(names) or any(not re.fullmatch(r'[A-Za-z0-9_-]+', s) for s in names):
        parser.error('Names must be unique safe filenames')
    if args.verify_existing:
        try:
            verified = verify_report(args.report, args.image, args.output)
            if list(verified) != [name + '.png' for name in names]:
                raise GridError('Requested filename order differs from validated mapping')
        except (GridError, KeyError, FileNotFoundError) as error:
            parser.exit(2, f'REJECTED: {error}\n')
        print(f'Verified {len(verified)} existing images against the measured source sheet')
        return
    try:
        with Image.open(args.image) as image:
            size = list(image.size)
            prepared, geometry = extract(image, args.columns, args.rows, method=args.method)
    except GridError as error:
        parser.exit(2, f'REJECTED: {error}\nNo images were written. Regenerate the source sheet.\n')
    paths = [args.output / f'{name}.png' for name in names]
    if any(p.exists() for p in paths) or args.report.exists():
        parser.error('Refusing to overwrite assets or a validation report')
    args.output.mkdir(parents=True, exist_ok=True)
    entries = []
    for path, (image, check) in zip(paths, prepared):
        image.save(path, optimize=True)
        entries.append({**check, 'file': path.name,
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    report = {'version': 1, 'passed': True, 'method': args.method,
              'sourceSha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
              'sourceSize': size, 'columns': args.columns, 'rows': args.rows,
              **geometry, 'tiles': entries}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Validated and extracted {len(entries)} tiles; report: {args.report}')


if __name__ == '__main__':
    main()
