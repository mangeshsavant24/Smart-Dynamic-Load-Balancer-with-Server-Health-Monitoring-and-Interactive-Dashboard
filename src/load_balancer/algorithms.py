from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests

from src.load_balancer.config import BACKENDS, BackendServer


@dataclass
class BackendState:
    server: BackendServer
    active_connections: int = 0
    last_cpu_percent: float = 0.0
    healthy: bool = True


class LoadBalancingAlgorithms:
    """
    Implements different load balancing strategies over a shared
    list of backend states.
    """

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self._states: List[BackendState] = [BackendState(server=b) for b in BACKENDS]
        self._rr_index: int = 0
        self._lock = threading.Lock()
        self._session = session or requests.Session()

    @property
    def states(self) -> List[BackendState]:
        return self._states


    # -------------------------
    # Strategy Implementations
    # -------------------------

    def next_round_robin(self) -> BackendState:
        """Simple round-robin selection among healthy backends."""

        with self._lock:
            healthy = [s for s in self._states if s.healthy]
            if not healthy:
                # fall back to all backends if none marked healthy
                healthy = self._states

            state = healthy[self._rr_index % len(healthy)]
            self._rr_index = (self._rr_index + 1) % len(healthy)
            return state

    def next_least_connections(self) -> BackendState:
        """Pick backend with the fewest active connections."""

        with self._lock:
            healthy = [s for s in self._states if s.healthy]
            candidates = healthy or self._states
            return min(candidates, key=lambda s: s.active_connections)

    def update_cpu_from_health(self) -> None:
        """
        Query /health of each backend to refresh CPU metrics.
        This is used by the CPU-based strategy.
        """

        for state in self._states:
            try:
                resp = self._session.get(f"{state.server.base_url}/health", timeout=0.5)
                if resp.status_code == 200:
                    data: Dict = resp.json()
                    state.last_cpu_percent = float(data.get("cpu_percent", 0.0))
                    state.healthy = data.get("status", "ok") == "ok"
                else:
                    state.healthy = False
            except Exception:
                state.healthy = False

    def next_cpu_based(self) -> BackendState:
        """
        Pick backend with the lowest recent CPU usage.
        CPU metrics are refreshed via /health on each call.
        """

        self.update_cpu_from_health()
        with self._lock:
            healthy = [s for s in self._states if s.healthy]
            candidates = healthy or self._states
            return min(candidates, key=lambda s: s.last_cpu_percent)


    # -------------------------
    # Connection Count Helpers
    # -------------------------

    def increment_connections(self, backend: BackendState) -> None:
        with self._lock:
            backend.active_connections += 1

    def decrement_connections(self, backend: BackendState) -> None:
        with self._lock:
            if backend.active_connections > 0:
                backend.active_connections -= 1

