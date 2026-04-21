import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import LOG_DIR


def get_logger(name: str = "load_balancer") -> logging.Logger:
    """
    Configure and return a logger that writes routing decisions to a file.
    """

    log_file = Path(LOG_DIR) / "routing.log"
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

