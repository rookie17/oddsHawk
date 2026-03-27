# utils/logger.py — Logging setup for OddsHawk

import logging
import sys

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if get_logger is called twice
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Format: [2024-05-01 14:32:01] [OddsHawk] INFO — message
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger