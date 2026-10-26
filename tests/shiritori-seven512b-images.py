"""Recompute every measured source crop and validate only the complementary 512-row change."""
import subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-B','-X','utf8',str(root/'scripts/finalize-shiritori-seven512b-images.py'),'verify'],cwd=root,check=True)
