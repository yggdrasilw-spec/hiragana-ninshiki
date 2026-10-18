"""Data/synthesis regression checks; no TensorFlow or ETL data required."""
import ast
import csv
import json
from pathlib import Path
import random
import tempfile
import unittest
import zipfile
import io

import numpy as np
from PIL import Image, ImageDraw
import katakana_training as k


class SynthesisTests(unittest.TestCase):
    def setUp(self):
        self.base = Image.new("L", (64, 64))
        ImageDraw.Draw(self.base).line([(10, 12), (47, 12), (44, 50), (30, 40)], fill=255, width=5)

    def test_labels_and_mark_geometry(self):
        self.assertEqual(len(k.LABELS), 72)
        self.assertEqual(len(set(k.LABELS)), 72)
        self.assertEqual(k.LABELS[:46], k.BASE_LABELS)
        self.assertIn("ヴ", k.LABELS)
        for seed in range(100):
            for layout in ("natural", "compact"):
                for kind in (None, "dakuten", "handakuten"):
                    image = k.compose(self.base, kind, seed, layout)
                    self.assertEqual(image.size, (64, 64))
                    box = k.tight(image).size
                    self.assertTrue(50 <= max(box) <= 58)
                    self.assertEqual(image.tobytes(), k.compose(self.base, kind, seed, layout).tobytes())
        with self.assertRaises(ValueError):
            k.draw_mark("unknown", random.Random(0))

    def test_polarity_and_blank_detection(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "image.png"
            self.base.save(path)
            a = k.ink_image(path).tobytes()
            Image.fromarray(255 - np.asarray(self.base)).save(path)
            self.assertEqual(a, k.ink_image(path).tobytes())
            Image.new("L", (64, 64), 255).save(path)
            with self.assertRaises(ValueError):
                k.ink_image(path)

    def test_mark_distance_uses_ink_and_covers_close_and_far(self):
        # A horizontal top, slant, curve and hollow ring have very different
        # empty corners. Measure independently from the dilation implementation.
        close = far = 0
        for shape in range(4):
            canvas = Image.new('L', (128, 128))
            draw = ImageDraw.Draw(canvas)
            if shape == 0:
                draw.line([(10, 35), (94, 35), (94, 110)], fill=255, width=5)
            elif shape == 1:
                draw.line([(90, 35), (20, 110)], fill=255, width=5)
            elif shape == 2:
                draw.arc((10, 35, 94, 110), 0, 320, fill=255, width=5)
            else:
                draw.ellipse((10, 35, 94, 110), outline=255, width=5)
            base_points = np.argwhere(np.asarray(canvas) > 10)
            for seed in range(50):
                rng = random.Random(seed)
                mark = k.draw_mark('dakuten' if seed % 2 else 'handakuten', rng).resize((23, 23))
                mx, my, target_gap = k.place_mark(canvas, mark, (10, 35, 85, 76), rng)
                points = np.argwhere(np.asarray(mark) > 10) + [my, mx]
                distance = np.abs(points[:, None, :] - base_points[None, :, :]).max(axis=2).min()
                self.assertGreaterEqual(distance, target_gap)
                self.assertLessEqual(distance, target_gap + 1)
                self.assertGreaterEqual(mx, 2)
                self.assertLessEqual(mx + mark.width, 126)
                self.assertGreaterEqual(my, 2)
                self.assertLessEqual(my + mark.height, 126)
                close += target_gap <= 6
                far += target_gap >= 7
        self.assertGreater(close, far)
        self.assertGreater(far, 0)

    def test_hand_drawn_mark_and_wide_top(self):
        with tempfile.TemporaryDirectory() as temp:
            donor = Path(temp) / 'mark.png'
            k.draw_mark('handakuten', random.Random(4)).save(donor)
            for seed in range(30):
                for layout in ('natural', 'compact'):
                    self.assertEqual(k.compose(self.base, 'handakuten', seed, layout, donor).size, (64, 64))

    def test_full_width_top_has_room_for_largest_gap(self):
        base = Image.new('L', (64, 64))
        ImageDraw.Draw(base).line([(4, 4), (59, 4), (59, 59), (4, 59)], fill=255, width=5)
        for seed in range(100):
            for kind in ('dakuten', 'handakuten'):
                self.assertEqual(k.compose(base, kind, seed).size, (64, 64))

    def test_sources_stay_together_before_expansion(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            csv_rows = []
            for char_id, char in enumerate(k.BASE_LABELS):
                folder = root / char
                folder.mkdir()
                for writer in range(50):
                    rng = random.Random(char_id * 10000 + writer)
                    im = self.base.copy()
                    # A small unique pattern stands in for an independent source.
                    draw = ImageDraw.Draw(im)
                    for _ in range(8):
                        x, y = rng.randrange(15, 45), rng.randrange(18, 45)
                        draw.rectangle((x, y, x+2, y+2), fill=rng.randrange(30, 230))
                    name = f"{writer:03d}.png"
                    im.save(folder / name)
                    csv_rows.append({"path": f"{char}/{name}", "group": f"writer-{writer}"})
                # Exact duplicate removed, same group required.
                (folder / "duplicate.png").write_bytes((folder / "000.png").read_bytes())
                csv_rows.append({"path": f"{char}/duplicate.png", "group": "writer-0"})
            groups_path = root / "groups.csv"
            with groups_path.open("w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["path", "group"])
                writer.writeheader()
                writer.writerows(csv_rows)
            rows, audit = k.inventory(root, groups_path)
            self.assertEqual(audit["removed_exact_duplicates"], 46)
            examples = k.make_examples(rows)
            self.assertEqual(set(r["label"] for r in examples), set(k.LABELS))
            group_splits = {}
            for row in examples:
                group_splits.setdefault(row["group"], set()).add(row["split"])
                if row["kind"] == "handakuten":
                    self.assertIn(row["label"], "パピプペポ")
            self.assertTrue(all(len(splits) == 1 for splits in group_splits.values()))
            self.assertEqual({r["split"] for r in examples}, {"train", "val", "test"})
            # All targets get exactly the same number of examples per class.
            from collections import Counter
            counts = Counter(r["label"] for r in examples)
            self.assertEqual(len(set(counts.values())), 1)
            k.preview(examples, root, root / "preview.png")
            self.assertTrue((root / "preview.json").is_file())
            self.assertEqual(rows, k.inventory(root, groups_path)[0])
            # Missing provenance cannot silently degrade to ungrouped splitting.
            groups_path.write_text("path,group\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                k.inventory(root, groups_path)

    def test_notebook_code_and_embedded_module(self):
        notebook = json.loads((Path(__file__).parent / "etl5_train_marks.ipynb").read_text(encoding="utf-8"))
        embedded = None
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                source = "".join(cell["source"])
                ast.parse("\n".join(line for line in source.splitlines() if not line.startswith("%")))
                if k.VERSION in source:
                    embedded = source.split("\n", 1)[1]
                self.assertFalse(cell["outputs"])
        self.assertEqual(embedded.strip(), (Path(__file__).parent / "katakana_training.py").read_text(encoding="utf-8").strip())

    def test_local_staging_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            source, local = Path(temp) / "drive", Path(temp) / "local"
            (source / "ｶ").mkdir(parents=True)
            self.base.save(source / "ｶ" / "one.png")
            k.stage_dataset(source, local, reserve_bytes=0, progress=False)
            self.assertEqual((source / "ｶ" / "one.png").read_bytes(), (local / "ｶ" / "one.png").read_bytes())
            k.stage_dataset(source, local, reserve_bytes=0, progress=False)
            report = json.loads((local / ".transfer.json").read_text())
            self.assertEqual((report["copied"], report["reused"]), (0, 1))
            (local / "ｶ" / "one.png").write_bytes(b"partial")
            k.stage_dataset(source, local, reserve_bytes=0, progress=False)
            self.assertEqual((source / "ｶ" / "one.png").read_bytes(), (local / "ｶ" / "one.png").read_bytes())
            with self.assertRaises(ValueError):
                k.stage_dataset(source, source / "nested", reserve_bytes=0, progress=False)
            (local / "ｶ" / "stale.png").write_bytes(b"stale")
            with self.assertRaises(ValueError):
                k.stage_dataset(source, local, reserve_bytes=0, progress=False)

    def test_zip_extraction_root_detection_and_resume(self):
        buffer = io.BytesIO()
        self.base.save(buffer, format="PNG")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for prefix in ("", "processed_dataset/"):
                archive = root / ("nested.zip" if prefix else "flat.zip")
                with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                    for char in k.BASE_LABELS:
                        bundle.writestr(f"{prefix}{char}/one.png", buffer.getvalue())
                extracted = Path(k.extract_dataset_zip(archive, root / "out", reserve_bytes=0, progress=False))
                self.assertEqual((extracted / "カ/one.png").read_bytes(), buffer.getvalue())
                self.assertEqual(len(list(extracted.glob("*/*.png"))), 46)
                self.assertEqual(str(extracted), k.extract_dataset_zip(archive, root / "out", reserve_bytes=0, progress=False))
                (extracted / "カ/one.png").write_bytes(b"partial")
                k.extract_dataset_zip(archive, root / "out", reserve_bytes=0, progress=False)
                self.assertEqual((extracted / "カ/one.png").read_bytes(), buffer.getvalue())
            bad = root / "bad.zip"
            with zipfile.ZipFile(bad, "w") as bundle:
                bundle.writestr("../escape.png", buffer.getvalue())
            with self.assertRaises(ValueError):
                k.extract_dataset_zip(bad, root / "out", reserve_bytes=0, progress=False)

    def test_three_drive_zip_parts(self):
        buffer = io.BytesIO()
        self.base.save(buffer, format="PNG")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parts = []
            for part in range(3):
                archive = root / f"download-{part:03d}.zip"
                parts.append(archive)
                with zipfile.ZipFile(archive, "w") as bundle:
                    for i, char in enumerate(k.BASE_LABELS):
                        if i % 3 == part:
                            bundle.writestr(f"processed_dataset-{part}/{char}/one.png", buffer.getvalue())
            local = Path(k.extract_dataset_zip(parts, root / "out", reserve_bytes=0, progress=False))
            self.assertEqual(len(list(local.glob("*/*.png"))), 46)
            self.assertEqual(str(local), k.extract_dataset_zip(parts[::-1], root / "out", reserve_bytes=0, progress=False))
            with self.assertRaises(ValueError):
                k.extract_dataset_zip(parts[:2], root / "out", reserve_bytes=0, progress=False)
            bad = root / "missing.zip"
            with zipfile.ZipFile(bad, "w") as bundle:
                bundle.writestr("dataset/カ/one.png", buffer.getvalue())
            with self.assertRaises(ValueError):
                k.extract_dataset_zip(bad, root / "out", reserve_bytes=0, progress=False)

    def test_partial_real_handwriting_zip(self):
        buffer = io.BytesIO()
        self.base.save(buffer, format="PNG")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "real-katakana-test.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                for char in "ガパヴ":
                    bundle.writestr(f"{char}/sample.png", buffer.getvalue())
                bundle.writestr("manifest.json", "{}")
                bundle.writestr("strokes/sample.json", "{}")
            local = Path(k.extract_dataset_zip(archive, root / "out", reserve_bytes=0,
                                              progress=False, labels=k.LABELS, require_all=False))
            self.assertEqual(len(list(local.glob("*/*.png"))), 3)


if __name__ == "__main__":
    unittest.main()
