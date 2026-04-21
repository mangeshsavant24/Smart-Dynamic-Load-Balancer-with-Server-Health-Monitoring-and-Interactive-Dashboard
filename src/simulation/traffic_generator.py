"""
Simple multithreaded traffic generator against the load balancer.

Usage (from project root):

    python src\\simulation\\traffic_generator.py --concurrency 20 --requests 200
"""

import argparse
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


def worker(base_url: str, idx: int) -> None:
    """Send a mix of compute and echo requests."""

    session = requests.Session()
    try:
        if idx % 2 == 0:
            n = random.randint(28, 32)
            session.get(f"{base_url}/api/compute?n={n}", timeout=5)
        else:
            payload = {"msg_index": idx, "text": "hello from load generator"}
            session.post(f"{base_url}/api/echo", json=payload, timeout=5)
    except Exception:
        # errors are acceptable in stress tests; just ignore
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Traffic generator for load balancer")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL of the load balancer",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=10,
        help="Number of concurrent worker threads",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=100,
        help="Total number of requests to send",
    )
    args = parser.parse_args()

    print(
        f"Sending {args.requests} requests to {args.base_url} "
        f"with concurrency={args.concurrency}"
    )

    start = time.time()
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker, args.base_url, i) for i in range(args.requests)]
        for _ in as_completed(futures):
            pass
    duration = time.time() - start

    print(f"Completed {args.requests} requests in {duration:.2f} seconds")


if __name__ == "__main__":
    # Ensure threads exit on Ctrl+C
    threading.current_thread().name = "main"
    main()

