import importlib.util,unittest
from pathlib import Path
from PIL import ImageDraw
import numpy as np
spec=importlib.util.spec_from_file_location('regression',Path(__file__).with_name('test-shiritori-grid-crop.py'))
reg=importlib.util.module_from_spec(spec);spec.loader.exec_module(reg)
grid=reg.module

class FullColorTests(unittest.TestCase):
 def test_local_horizontal_halo_at_a_junction_is_not_a_wide_vertical_line(self):
  image=reg.sheet();draw=ImageDraw.Draw(image)
  draw.line((406,8,440,8),fill=(255,235,255),width=1)
  out,geometry=grid.extract(image)
  self.assertEqual(geometry['rowBands'][0],[0,9])
  self.assertEqual(geometry['columnBands'][2],[398,406])
  self.assertEqual(out[2][1]['cropBox'][:2],[406,9])

 def test_crossing_fringe_does_not_expand_into_the_other_divider(self):
  image=reg.sheet();draw=ImageDraw.Draw(image)
  draw.line((8,8,250,8),fill=(255,235,255),width=1)
  draw.line((8,8,8,180),fill=(255,235,255),width=1)
  out,_=grid.extract(image)
  self.assertEqual(out[0][1]['cropBox'],[9,9,194,194])

 def test_disconnected_pink_does_not_trim_a_column_of_artwork(self):
  image=reg.sheet();draw=ImageDraw.Draw(image)
  draw.rectangle((204,40,220,80),fill=(255,235,255))
  draw.rectangle((202,100,240,140),fill=(20,40,80))
  out,_=grid.extract(image)
  self.assertEqual(out[1][1]['cropBox'][0],202)
  self.assertGreater(out[1][1]['edgeInkFraction'],0)

 def test_sparse_fringe_beyond_one_search_window_is_measured(self):
  image=reg.sheet();draw=ImageDraw.Draw(image)
  draw.rectangle((202,40,207,45),fill=(255,235,255))
  draw.rectangle((208,80,260,120),fill=(20,40,80))
  out,_=grid.extract(image)
  self.assertEqual(out[1][1]['cropBox'][0],208)
  self.assertGreater(out[1][1]['edgeInkFraction'],0)

 def test_wide_pink_region_cannot_be_removed_as_a_fringe(self):
  image=reg.sheet();ImageDraw.Draw(image).rectangle((202,40,260,80),fill=(255,235,255))
  with self.assertRaises(grid.GridError):grid.extract(image)

 def test_purple_and_pink_art_are_preserved(self):
  image=reg.sheet();draw=ImageDraw.Draw(image)
  draw.rectangle((8,8,180,90),fill=(220,60,220))
  draw.rectangle((8,91,180,180),fill=(255,210,240))
  out,geometry=grid.extract(image)
  self.assertEqual(geometry['columnBands'][1],[194,202])
  self.assertEqual(out[0][1]['cropBox'],[8,8,194,194])
  colors=np.asarray(out[0][0]);self.assertTrue(np.any(np.all(colors==(220,60,220),axis=2)))
  self.assertTrue(np.any(np.all(colors==(255,210,240),axis=2)))

 def test_real_magenta_contamination_is_still_rejected(self):
  image=reg.sheet();ImageDraw.Draw(image).rectangle((40,40,60,60),fill=(255,0,255))
  with self.assertRaises(grid.GridError):grid.extract(image)

 def test_unequal_rows_remain_rejected(self):
  from PIL import Image
  image=Image.new('RGB',(800,800),'white');draw=ImageDraw.Draw(image)
  xs=[3,197,401,599,796];ys=[3,197,401,560,796]
  for x in xs:draw.line((x,0,x,799),fill=(255,0,255),width=8)
  for y in ys:draw.line((0,y,799,y),fill=(255,0,255),width=8)
  for row in range(4):
   for col in range(4):draw.ellipse((xs[col]+30,ys[row]+30,xs[col]+80,ys[row]+80),fill='green')
  with self.assertRaises(grid.GridError):grid.extract(image)

if __name__=='__main__':unittest.main()
