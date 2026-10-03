import os
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parents[1]
os.chdir(root)
sys.path.insert(0, str(root / "services/api"))
runpy.run_module("app.seed", run_name="__main__")
