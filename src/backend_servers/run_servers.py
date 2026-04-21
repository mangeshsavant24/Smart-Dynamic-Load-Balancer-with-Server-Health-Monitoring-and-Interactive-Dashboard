"""
Helper script to start three backend Flask servers on different ports.

Usage (from project root):

    python -m src.backend_servers.run_servers
"""

from .server_app import run_multiple_servers


if __name__ == "__main__":
    run_multiple_servers()

