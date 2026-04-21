"""
Helper script to start three backend Flask servers on different ports.

Usage (from project root):

    python src\backend_servers\run_servers.py
    or
    python -m src.backend_servers.run_servers
"""

from pathlib import Path
import sys

# Ensure project root is on sys.path so that `src.*` imports work
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.backend_servers.server_app import run_multiple_servers


if __name__ == "__main__":
    run_multiple_servers()

