"""Reproduce four deterministic wave6 diagrams without overwriting assets."""
import argparse
import math
from pathlib import Path
from PIL import Image, ImageDraw

def build():
    for row_id, color in [(10, '#2878df'), (15, '#e33232'), (514, '#f4b3b3'), (519, None)]:
        picture = Image.new('RGB', (768, 768), 'white')
        draw = ImageDraw.Draw(picture)
        if color:
            draw.ellipse((96, 96, 672, 672), fill=color)
        else:
            points = []
            for n in range(1201):
                theta = n / 1200 * math.pi * 6
                radius = 270 * (1 - n / 1200)
                points.append((384 + math.cos(theta) * radius, 384 + math.sin(theta) * radius))
            draw.line(points, fill='#2454a0', width=18, joint='curve')
        yield row_id, picture.resize((256, 256), Image.Resampling.LANCZOS)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepared = list(build())
    if any((args.output / f'wave6-word-{row_id}.png').exists() for row_id, _ in prepared):
        parser.error('Refusing to overwrite existing diagrams')
    args.output.mkdir(parents=True, exist_ok=True)
    for row_id, image in prepared:
        image.save(args.output / f'wave6-word-{row_id}.png', optimize=True)
