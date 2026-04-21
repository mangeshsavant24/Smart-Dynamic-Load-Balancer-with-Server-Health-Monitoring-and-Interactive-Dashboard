import pathlib
from dataclasses import dataclass
from typing import List


BASE_DIR = pathlib.Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
DB_DIR = BASE_DIR / "db"

LOG_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)


@dataclass
class BackendServer:
    name: str
    host: str
    port: int

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


BACKENDS: List[BackendServer] = [
    BackendServer(name="server-1", host="127.0.0.1", port=5001),
    BackendServer(name="server-2", host="127.0.0.1", port=5002),
    BackendServer(name="server-3", host="127.0.0.1", port=5003),
]

DEFAULT_ALGORITHM = "round_robin"  # options: round_robin, least_connections, cpu_based

LOAD_BALANCER_HOST = "127.0.0.1"
LOAD_BALANCER_PORT = 8000

