import sys
from pathlib import Path

# Resolve the project root folder and insert it into sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import the FastAPI application instance
from src.akshat_fastapi import app
