"""Regression tests for boundary detection, contamination, and fail-closed CLI."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/crop-shiritori-grid.py'
if not SCRIPT.is_file():
    SCRIPT = Path(__file__).resolve().with_name('crop-shiritori-grid.py')
spec = importlib.util.spec_from_file_location('grid_crop', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def sheet():
    picture = Image.new('RGB', (800, 800), 'white')
    draw = ImageDraw.Draw(picture)
    # Uneven positions deliberately test actual, rather than equal, borders.
    positions = [3, 197, 401, 599, 796]
    for p in positions:
        draw.line((p, 0, p, 799), fill=(255, 0, 255), width=8)
        draw.line((0, p, 799, p), fill=(255, 0, 255), width=8)
    for i in range(16):
        y, x = divmod(i, 4)
        draw.rectangle((x * 200 + 60, y * 200 + 60,
                        x * 200 + 135, y * 200 + 135), fill=(30 + i * 8, 80, 100))
    return picture


class CropTests(unittest.TestCase):
    def test_measured_boundaries_and_row_order(self):
        outputs, report = module.extract(sheet())
        self.assertEqual(len(outputs), 16)
        self.assertEqual(report['columnBands'][1], [194, 202])
        for i, (image, check) in enumerate(outputs):
            self.assertEqual(image.size, (256, 256))
            self.assertEqual(check['tileIndex'], i + 1)
            self.assertEqual(image.getpixel((128, 128)), (30 + i * 8, 80, 100))
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_pastel_art_next_to_line_is_not_a_fringe(self):
        image = sheet()
        ImageDraw.Draw(image).rectangle((50, 202, 89, 280), fill=(230, 210, 235))
        with self.assertRaises(module.GridError):
            module.extract(image, method='magenta-grid-lines-only-v2')
        outputs, _ = module.extract(image)
        self.assertEqual(outputs[4][1]['cropBox'], [8, 202, 194, 398])
        self.assertGreater(outputs[4][1]['contentFraction'], 0.01)

    def test_v2_report_is_still_reproducible(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as directory:
            root = Path(directory)
            source = root / 'sheet.png'
            sheet().save(source)
            old = SCRIPT
            subprocess.run([sys.executable, str(old), str(source), '--method', 'magenta-grid-lines-only-v2', '--names',
                            ','.join(f'tile-{i}' for i in range(16)), '--output',
                            str(root / 'out'), '--report', str(root / 'report.json')],
                           capture_output=True, check=True)
            self.assertEqual(len(module.verify_report(root / 'report.json', source, root / 'out')), 16)

    def test_sparse_fringe_requires_stable_measured_bounds(self):
        image = sheet()
        draw = ImageDraw.Draw(image)
        draw.rectangle((80, 190, 82, 190), fill=(255, 235, 255))
        draw.rectangle((80, 188, 82, 188), fill=(255, 235, 255))
        draw.rectangle((100, 182, 120, 187), fill=(20, 40, 80))
        with self.assertRaises(module.GridError):
            module.extract(image, method='magenta-grid-lines-only-v3')
        outputs, _ = module.extract(image)
        self.assertEqual(outputs[0][1]['cropBox'][3], 188)
        self.assertGreater(outputs[0][1]['edgeInkFraction'], 0)

    def test_missing_grid_rejected(self):
        with self.assertRaises(module.GridError):
            module.extract(Image.new('RGB', (800, 800), 'white'))

    def test_broken_line_rejected(self):
        image = sheet()
        ImageDraw.Draw(image).rectangle((0, 397, 450, 405), fill='white')
        with self.assertRaises(module.GridError):
            module.extract(image)

    def test_content_near_boundary_is_kept_without_large_margin(self):
        image = sheet()
        ImageDraw.Draw(image).rectangle((8, 8, 180, 180), fill=(0, 30, 100))
        outputs, _ = module.extract(image)
        self.assertGreater(outputs[0][1]['edgeInkFraction'], 0.005)
        self.assertEqual(outputs[0][1]['cropBox'], [8, 8, 194, 194])
        self.assertEqual(outputs[0][0].getpixel((1, 1)), (0, 30, 100))
        with self.assertRaises(module.GridError):
            module.extract(image, method='magenta-grid-white-guard-v1')

    def test_divider_residue_rejected(self):
        image = sheet()
        ImageDraw.Draw(image).rectangle((140, 140, 145, 145), fill=(255, 0, 255))
        with self.assertRaises(module.GridError):
            module.extract(image)

    def test_blank_cell_rejected(self):
        image = sheet()
        ImageDraw.Draw(image).rectangle((30, 30, 170, 170), fill='white')
        with self.assertRaises(module.GridError):
            module.extract(image)

    def test_antialiased_fringe_is_removed(self):
        image = sheet()
        draw = ImageDraw.Draw(image)
        for p in [3, 197, 401, 599, 796]:
            for q in [p - 4, p + 5]:
                draw.line((q, 0, q, 799), fill=(255, 213, 255), width=1)
                draw.line((0, q, 799, q), fill=(255, 213, 255), width=1)
        outputs, _ = module.extract(image)
        self.assertTrue(all(check['edgeInkFraction'] == 0 for _, check in outputs))

    def test_sparse_tinted_line_fringe_removed_without_cutting_dark_art(self):
        image = sheet()
        draw = ImageDraw.Draw(image)
        draw.rectangle((202, 40, 203, 45), fill=(255, 235, 255))
        draw.rectangle((204, 80, 260, 120), fill=(20, 40, 80))
        outputs, _ = module.extract(image)
        self.assertEqual(outputs[1][1]['cropBox'][0], 204)
        self.assertFalse(module.marker_mask(__import__('numpy').asarray(outputs[1][0])).any())
        self.assertGreater(outputs[1][1]['edgeInkFraction'], 0)

    def test_proof_is_recomputed_and_tampered_png_rejected(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as directory:
            root = Path(directory)
            source = root / 'sheet.png'
            sheet().save(source)
            names = ','.join(f'tile-{i}' for i in range(16))
            subprocess.run([sys.executable, str(SCRIPT), str(source), '--names', names,
                            '--output', str(root / 'out'), '--report', str(root / 'report.json')],
                           capture_output=True, check=True)
            verified = module.verify_report(root / 'report.json', source, root / 'out')
            self.assertEqual(len(verified), 16)
            victim = root / 'out/tile-0.png'
            Image.new('RGB', (256, 256), 'white').save(victim)
            with self.assertRaises(module.GridError):
                module.verify_report(root / 'report.json', source, root / 'out')

    def test_proof_source_and_tile_mapping_tamper_rejected(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as directory:
            root = Path(directory)
            source = root / 'sheet.png'
            sheet().save(source)
            report_path = root / 'report.json'
            subprocess.run([sys.executable, str(SCRIPT), str(source),
                            '--names', ','.join(f'tile-{i}' for i in range(16)),
                            '--output', str(root / 'out'), '--report', str(report_path)],
                           capture_output=True, check=True)
            report = json.loads(report_path.read_text())
            report['tiles'][0], report['tiles'][1] = report['tiles'][1], report['tiles'][0]
            report_path.write_text(json.dumps(report))
            with self.assertRaises(module.GridError):
                module.verify_report(report_path, source, root / 'out')
            sheet2 = sheet()
            ImageDraw.Draw(sheet2).point((80, 80), fill='red')
            sheet2.save(source)
            with self.assertRaises(module.GridError):
                module.verify_report(report_path, source, root / 'out')

    def test_bad_last_cell_does_not_write_first_fifteen(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent) as directory:
            root = Path(directory)
            image = sheet()
            ImageDraw.Draw(image).rectangle((630, 630, 770, 770), fill='white')
            source = root / 'source.png'
            image.save(source)
            result = subprocess.run([sys.executable, str(SCRIPT), str(source),
                                     '--names', ','.join(f'tile-{i}' for i in range(16)),
                                     '--output', str(root / 'out'),
                                     '--report', str(root / 'report.json')], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((root / 'out').exists())
            self.assertFalse((root / 'report.json').exists())


if __name__ == '__main__':
    unittest.main()
