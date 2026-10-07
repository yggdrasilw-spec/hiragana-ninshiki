"""Crop a regular generated contact sheet into square shiritori image assets.

Usage:
  python scripts/crop-shiritori-grid.py input.png --columns 4 --rows 4 \
    --names kansha,souzou,kufuu,...

Tile names are emitted as 256px PNGs in assets/shiritori. A small margin is
trimmed from each equal-sized grid cell to avoid retaining divider gutters.
"""
import argparse
from pathlib import Path
from PIL import Image


parser = argparse.ArgumentParser()
parser.add_argument("image", type=Path)
parser.add_argument("--columns", type=int, required=True)
parser.add_argument("--rows", type=int, required=True)
parser.add_argument("--names", required=True, help="Comma-separated tile names in reading order")
parser.add_argument("--output", type=Path, default=Path("assets/shiritori"))
parser.add_argument("--margin", type=float, default=0.025, help="Fraction trimmed from each cell edge")
args = parser.parse_args()

names = [name.strip() for name in args.names.split(",")]
if len(names) != args.columns * args.rows:
    parser.error("--names must contain exactly rows × columns names")
if any(not name or not all(ch.isalnum() or ch in "-_" for ch in name) for name in names):
    parser.error("tile names may contain only letters, numbers, hyphens, and underscores")
if not 0 <= args.margin < 0.25:
    parser.error("--margin must be between 0 and 0.25")

image = Image.open(args.image).convert("RGB")
cell_w, cell_h = image.width / args.columns, image.height / args.rows
args.output.mkdir(parents=True, exist_ok=True)
for index, name in enumerate(names):
    row, col = divmod(index, args.columns)
    inset_x, inset_y = cell_w * args.margin, cell_h * args.margin
    box = (
        round(col * cell_w + inset_x),
        round(row * cell_h + inset_y),
        round((col + 1) * cell_w - inset_x),
        round((row + 1) * cell_h - inset_y),
    )
    image.crop(box).resize((256, 256), Image.Resampling.LANCZOS).save(
        args.output / f"{name}.png", optimize=True
    )
print(f"Cropped {len(names)} tiles into {args.output}")
