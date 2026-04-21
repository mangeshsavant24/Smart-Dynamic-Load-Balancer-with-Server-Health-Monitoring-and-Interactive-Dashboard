import time
import threading
from typing import Any, Dict

import psutil
from flask import Flask, jsonify, request

app = Flask(__name__)


def create_app(server_id: str) -> Flask:
    """
    Factory to create a Flask app instance tagged with a server_id.
    This allows running multiple servers (different ports) with the same code.
    """

    app.config["SERVER_ID"] = server_id
    return app


@app.route("/api/compute")
def compute() -> Any:
    """
    Simulate a CPU-intensive task (e.g., computing Fibonacci).
    Query param: n (int) controls the workload.
    """

    try:
        n = int(request.args.get("n", "30"))
    except ValueError:
        n = 30

    def fib(k: int) -> int:
        if k <= 1:
            return k
        return fib(k - 1) + fib(k - 2)

    start = time.time()
    result = fib(max(0, min(n, 35)))  # cap to avoid extreme CPU usage
    duration = time.time() - start

    return jsonify(
        {
            "server_id": app.config.get("SERVER_ID", "unknown"),
            "operation": "fib",
            "n": n,
            "result": result,
            "duration_sec": round(duration, 4),
        }
    )


@app.route("/api/echo", methods=["POST"])
def echo() -> Any:
    """Simple echo endpoint for functional testing."""

    payload: Dict[str, Any] = request.get_json(silent=True) or {}
    return jsonify(
        {
            "server_id": app.config.get("SERVER_ID", "unknown"),
            "message": "Echo from backend server",
            "payload": payload,
        }
    )


@app.route("/health")
def health() -> Any:
    """
    Lightweight health check endpoint.
    Used by the load balancer for health monitoring and CPU-based routing.
    """

    process = psutil.Process()
    cpu_percent = process.cpu_percent(interval=0.05)
    mem_info = process.memory_info()

    return jsonify(
        {
            "server_id": app.config.get("SERVER_ID", "unknown"),
            "status": "ok",
            "cpu_percent": cpu_percent,
            "memory_rss_mb": round(mem_info.rss / (1024 * 1024), 2),
            "timestamp": time.time(),
        }
    )


def run_server(port: int, server_id: str) -> None:
    """
    Run a single Flask server instance on the given port.
    Intended to be called from a threading.Thread.
    """

    local_app = create_app(server_id)
    local_app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)


def run_multiple_servers() -> None:
    """
    Convenience function to run three backend servers on ports
    5001, 5002, 5003 using separate threads.
    """

    configs = [(5001, "server-1"), (5002, "server-2"), (5003, "server-3")]
    threads = []

    for port, sid in configs:
        t = threading.Thread(target=run_server, args=(port, sid), daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    # Default to running multiple servers when this file is executed directly.
    run_multiple_servers()

