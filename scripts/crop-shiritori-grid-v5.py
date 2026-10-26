"""Fail-closed extraction of marked vocabulary sheets, without large margins.

The generator must draw uninterrupted magenta grid lines, including outer
borders. Remove only measured divider lines and their fringes. No equal-quarter
fallback, manual crop override, or output is allowed when validation fails.
"""
import argparse
import importlib.util
import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


_previous_spec = importlib.util.spec_from_file_location('grid_crop_v3', Path(__file__).with_name('crop-shiritori-grid-v4.py'))
previous = importlib.util.module_from_spec(_previous_spec)
_previous_spec.loader.exec_module(previous)
legacy = previous.legacy


GridError = legacy.GridError


def marker_mask(rgb):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    # Identify actual magenta ink, rather than ordinary violet/pink artwork.
    return (r >= 225) & (b >= 225) & (g <= 70) & (abs(r - b) <= 35)


def divider_fringe_mask(rgb):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    # Magenta blended with white has almost equal, almost-maximal R and B.
    # Ordinary purple/pink watercolor must not inflate measured divider bands.
    return (r >= 245) & (b >= 245) & (g <= 240) & (abs(r - b) <= 3)


def line_bands(mask, axis, count, fringe=None):
    support = mask.mean(axis=axis)
    indices = np.flatnonzero(support >= 0.94)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    groups = [g for g in groups if len(g)]
    length = len(support)
    fringe_support = (fringe if fringe is not None else mask).mean(axis=axis)
    fringe_threshold = 0.90  # Full-length faint lines, not isolated colored artwork.
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


def refine_tinted_edges(rgb, bands, perpendicular, axis):
    r, g, b = [rgb[:, :, i].astype(int) for i in range(3)]
    tint = (r >= 245) & (b >= 245) & (g <= 240) & (abs(r - b) <= 3)
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


def connected_divider_geometry(rgb, xs, ys):
    """Flood only ink connected in TWO dimensions to a measured divider.

    A pink flower or glow elsewhere in the same column is not a divider.
    Broad or bridged components still fail closed rather than trimming art.
    """
    eligible = divider_fringe_mask(rgb) | marker_mask(rgb)
    ink = np.zeros(eligible.shape, dtype=bool)
    results = []
    for axis, cores, perpendicular in ((0, xs, ys), (1, ys, xs)):
        plane = eligible if axis == 0 else eligible.T
        length = plane.shape[1]
        maximum = length * 0.025
        search = int(np.ceil(maximum)) + 2
        bands = []
        for index, (lo, hi) in enumerate(cores):
            begin, end = max(0, lo - search), min(length, hi + search)
            allowed = plane[:, begin:end].copy()
            reached = np.zeros(allowed.shape, dtype=bool)
            reached[:, lo-begin:hi-begin] = True
            for lower, upper in perpendicular:
                allowed[lower:upper, :] = False
                reached[lower:upper, :] = False
            for iteration in range(256):
                expanded = reached.copy()
                expanded[1:, :] |= reached[:-1, :]
                expanded[:-1, :] |= reached[1:, :]
                expanded[:, 1:] |= reached[:, :-1]
                expanded[:, :-1] |= reached[:, 1:]
                expanded[1:, 1:] |= reached[:-1, :-1]
                expanded[:-1, :-1] |= reached[1:, 1:]
                expanded[1:, :-1] |= reached[:-1, 1:]
                expanded[:-1, 1:] |= reached[1:, :-1]
                updated = reached | (expanded & allowed)
                occupied = np.flatnonzero(updated.any(axis=0))
                first, last = begin + int(occupied[0]), begin + int(occupied[-1]) + 1
                if last - first > maximum:
                    raise GridError('Wide connected divider component; preserving artwork requires a repaired sheet')
                if np.array_equal(updated, reached):
                    reached = updated
                    break
                reached = updated
            else:
                raise GridError('Connected divider measurement did not converge')
            if abs((first + last - 1) / 2 - index * (length - 1) / 4) > maximum:
                raise GridError('Connected divider is displaced beyond layout tolerance')
            bands.append([first, last])
            if axis == 0:
                ink[:, begin:end] |= reached
            else:
                ink[begin:end, :] |= reached.T
        results.append(bands)
    return results[0], results[1], ink


def extract(image, columns=4, rows=4, method='magenta-grid-full-color-v5'):
    if method == 'magenta-grid-full-color-v4':
        return previous.extract(image, columns, rows, method=method)
    if method == 'magenta-grid-full-color-v3':
        return previous.extract(image, columns, rows, method=method)
    if method in ('magenta-grid-white-guard-v1', 'magenta-grid-lines-only-v2'):
        return legacy.extract(image, columns, rows, method=method)
    image = image.convert('RGB')
    rgb = np.asarray(image)
    if min(image.size) < max(columns, rows) * 96:
        raise GridError('Source resolution is too small')
    # Broad candidate mask retains the original 94% continuity requirement.
    mask = legacy.marker_mask(rgb)
    fringe = divider_fringe_mask(rgb)
    xs = line_bands(mask, 0, columns, fringe)
    ys = line_bands(mask, 1, rows, fringe)
    if method == 'magenta-grid-full-color-v5':
        xs, ys, frame_ink = connected_divider_geometry(rgb, xs, ys)
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
        if method == 'magenta-grid-full-color-v5':
            if frame_ink[box[1]:box[3], box[0]:box[2]].any():
                raise GridError(f'Tile {index + 1}: connected divider ink remains inside the crop')
        result = ImageOps.pad(image.crop(box), (256, 256),
                              method=Image.Resampling.LANCZOS, color='white')
        prepared.append((result, {'tileIndex': index + 1, 'cropBox': box,
                                  'edgeInkFraction': edge_fraction,
                                  'contentFraction': content_fraction}))
    return prepared, {'columnBands': xs, 'rowBands': ys}


def verify_report(report_path, source_path, output_directory):
    """Recompute geometry and every PNG before trusting registration evidence."""
    report = json.loads(Path(report_path).read_text(encoding='utf-8'))
    if report.get('method') == 'magenta-grid-full-color-v4':
        return previous.verify_report(report_path, source_path, output_directory)
    if report.get('method') == 'magenta-grid-full-color-v3':
        return previous.verify_report(report_path, source_path, output_directory)
    if report.get('method') in ('magenta-grid-white-guard-v1', 'magenta-grid-lines-only-v2'):
        return legacy.verify_report(report_path, source_path, output_directory)
    if (report.get('version') != 1 or report.get('passed') is not True
            or report.get('method') not in ('magenta-grid-white-guard-v1', 'magenta-grid-full-color-v5')
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
            prepared, geometry = extract(image, args.columns, args.rows)
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
    report = {'version': 1, 'passed': True, 'method': 'magenta-grid-full-color-v5',
              'sourceSha256': hashlib.sha256(args.image.read_bytes()).hexdigest(),
              'sourceSize': size, 'columns': args.columns, 'rows': args.rows,
              **geometry, 'tiles': entries}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Validated and extracted {len(entries)} tiles; report: {args.report}')


if __name__ == '__main__':
    main()
