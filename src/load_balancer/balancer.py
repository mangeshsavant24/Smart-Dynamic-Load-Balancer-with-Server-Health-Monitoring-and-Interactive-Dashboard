"""
Custom HTTP load balancer.

Exposes the same API surface as the backend servers and forwards
requests to one of the backend instances using a chosen algorithm:
- round_robin
- least_connections
- cpu_based
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
import sys
from typing import Any, Dict

import requests
from flask import Flask, Response, jsonify, request

# Ensure project root is on sys.path so that `src.*` imports work
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.load_balancer.algorithms import LoadBalancingAlgorithms
from src.load_balancer.config import BACKENDS, DEFAULT_ALGORITHM, LOAD_BALANCER_HOST, LOAD_BALANCER_PORT
from src.load_balancer.logger import get_logger
from src.monitoring.metrics_collector import log_local_cpu_memory, log_request


app = Flask(__name__)
logger = get_logger()
session = requests.Session()
algorithms = LoadBalancingAlgorithms(session=session)


def choose_backend(algorithm: str):
    if algorithm == "round_robin":
        return algorithms.next_round_robin()
    if algorithm == "least_connections":
        return algorithms.next_least_connections()
    if algorithm == "cpu_based":
        return algorithms.next_cpu_based()
    # fall back to round robin
    return algorithms.next_round_robin()


def forward_request(backend_base_url: str) -> Response:
    """
    Forward the incoming Flask request to the selected backend server.
    """

    path = request.full_path if request.query_string else request.path
    target_url = f"{backend_base_url}{path}"

    data = request.get_data()
    headers = dict(request.headers)
    headers.pop("Host", None)

    resp = session.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=data,
        timeout=5,
    )

    excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = [
        (name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers
    ]

    return Response(resp.content, resp.status_code, response_headers)


@app.before_request
def before_request_hook() -> None:
    # lightweight monitoring of LB process
    log_local_cpu_memory(backend_name="load_balancer")


def route_request(algorithm: str) -> Any:
    """
    Core routing logic shared by the exposed endpoints.
    Includes basic failover: if chosen backend fails, try others.
    """

    # first choice
    backend_state = choose_backend(algorithm)
    tried = set()

    while True:
        tried.add(backend_state.server.name)
        algorithms.increment_connections(backend_state)
        start = time.time()
        try:
            response = forward_request(backend_state.server.base_url)
            duration_ms = (time.time() - start) * 1000

            log_request(
                algorithm=algorithm,
                backend_name=backend_state.server.name,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=duration_ms,
            )

            logger.info(
                f"algorithm={algorithm} path={request.path} method={request.method} "
                f"backend={backend_state.server.name} status={response.status_code} "
                f"time_ms={duration_ms:.2f}"
            )

            return response
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.time() - start) * 1000
            logger.error(
                f"Request to backend {backend_state.server.name} failed: {exc}. "
                f"duration_ms={duration_ms:.2f}"
            )
            backend_state.healthy = False
            algorithms.decrement_connections(backend_state)

            # try a different backend
            remaining = [b for b in BACKENDS if b.name not in tried]
            if not remaining:
                return jsonify({"error": "All backends failed"}), 502

            # pick next candidate (round robin among remaining for simplicity)
            next_server = remaining[0]
            for s in algorithms.states:
                if s.server.name == next_server.name:
                    backend_state = s
                    break
        finally:
            algorithms.decrement_connections(backend_state)


@app.route("/api/compute", methods=["GET"])
def api_compute() -> Any:
    algorithm = app.config.get("ALGORITHM", DEFAULT_ALGORITHM)
    return route_request(algorithm)


@app.route("/api/echo", methods=["POST"])
def api_echo() -> Any:
    algorithm = app.config.get("ALGORITHM", DEFAULT_ALGORITHM)
    return route_request(algorithm)


@app.route("/health")
def lb_health() -> Any:
    """Health endpoint for the load balancer itself."""

    return jsonify(
        {
            "status": "ok",
            "algorithm": app.config.get("ALGORITHM", DEFAULT_ALGORITHM),
            "backends": [b.server.name for b in algorithms.states],
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Custom Python Load Balancer")
    parser.add_argument(
        "--algorithm",
        type=str,
        default=DEFAULT_ALGORITHM,
        choices=["round_robin", "least_connections", "cpu_based"],
        help="Load balancing algorithm to use",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    app.config["ALGORITHM"] = args.algorithm
    logger.info(f"Starting load balancer on {LOAD_BALANCER_HOST}:{LOAD_BALANCER_PORT} using {args.algorithm}")
    app.run(host=LOAD_BALANCER_HOST, port=LOAD_BALANCER_PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()

