import sys
from pathlib import Path

root = Path(__file__).parent.parent.resolve()

if str(root) not in sys.path:
    sys.path.insert(0, str(root))

for src_dir in root.glob("services/*/src"):
    if src_dir.is_dir() and str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

libs_dir = root / "libs"
if libs_dir.is_dir() and str(libs_dir) not in sys.path:
    sys.path.insert(0, str(libs_dir))
