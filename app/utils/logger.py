import logging
import sys

from app.utils.request_context import get_request_id


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("enterprise_agent")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    handler.addFilter(RequestIdFilter())

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | "
        "request_id=%(request_id)s | "
        "%(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()