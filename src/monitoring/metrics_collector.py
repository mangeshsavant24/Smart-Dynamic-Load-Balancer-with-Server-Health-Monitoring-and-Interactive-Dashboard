from __future__ import annotations

import time
from typing import Optional

import psutil

from src.monitoring.db import SessionLocal, init_db
from src.monitoring.models import HealthLog, RequestLog


def log_request(
    *,
    algorithm: str,
    backend_name: str,
    path: str,
    method: str,
    status_code: int,
    response_time_ms: float,
) -> None:
    """Persist a single request log entry."""

    init_db()
    db = SessionLocal()
    try:
        entry = RequestLog(
            algorithm=algorithm,
            backend_name=backend_name,
            path=path,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def log_local_cpu_memory(backend_name: Optional[str] = "load_balancer") -> None:
    """
    Log CPU and memory usage of the current process to the HealthLog table.
    This is used to monitor the load balancer host itself.
    """

    init_db()
    db = SessionLocal()
    try:
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.05)
        mem_info = process.memory_info()
        entry = HealthLog(
            backend_name=backend_name,
            cpu_percent=cpu_percent,
            memory_rss_mb=round(mem_info.rss / (1024 * 1024), 2),
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def timed_execution_ms(func, *args, **kwargs) -> float:
    """
    Helper to measure execution time of a callable in milliseconds.
    Returns: elapsed_ms, and also returns the function result via kwargs['__result__'] if passed.
    """

    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    elapsed_ms = (end - start) * 1000
    return elapsed_ms, result

