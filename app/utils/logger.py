import logging
import sys


def setup_logger() -> logging.Logger:
    """
    Configure application-wide logging.
    """

    logger = logging.getLogger("enterprise_agent")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()