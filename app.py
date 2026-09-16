"""Vercel entrypoint for SkillVerify's Flask application."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Import the actual Flask app from backend/app.py.
# Do not use `from app import app` here because this file is itself named app.py.
from backend.app import app  # noqa: E402,F401
