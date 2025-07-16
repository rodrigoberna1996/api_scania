import sys
from pathlib import Path

# Allow importing the 'app' package when running tests directly from the repo
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

