"""Illustrate the synthesis algorithm using font glyphs, not ETL training data."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import katakana_training as k

HERE = Path(__file__).resolve().parent
font_path = Path('C:/Windows/Fonts/meiryo.ttc')
font = ImageFont.truetype(str(font_path), 26)
glyph = ImageFont.truetype(str(font_path), 100)
chars = list('カキシツハホウ')
sheet = Image.new('RGB', (1120, 710), '#eef1f6')
draw = ImageDraw.Draw(sheet)
draw.text((22, 14), '濁点・半濁点の自動合成：動作例', font=font, fill='#172338')
draw.text((22, 52), 'フォント画像での説明用。ETL実筆データ・学習結果ではありません。', font=ImageFont.truetype(str(font_path), 21), fill='#43526a')
for col, char in enumerate(chars):
    base = Image.new('L', (140, 140))
    ImageDraw.Draw(base).text((8, 0), char, font=glyph, fill=255)
    variants = [(char, None), (k.VOICED[char], 'dakuten'),
                (k.SEMIVOICED.get(char), 'handakuten'), (k.VOICED[char], 'dakuten')]
    for row, (label, kind) in enumerate(variants):
        if not label:
            continue
        image = k.compose(base, kind, seed=col + row * 777)
        x, y = col * 157 + 13, row * 150 + 106
        sheet.paste(image.convert('RGB').resize((112, 112)), (x, y))
        draw.text((x+119, y+40), label, font=font, fill='#172338')
draw.text((22, 686), '上から：清音／濁音／半濁音／別の濁点バリエーション', font=ImageFont.truetype(str(font_path), 17), fill='#43526a')
sheet.save(HERE / 'synthesis-demo.png')
print(HERE / 'synthesis-demo.png')
