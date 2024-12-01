import logging

logger = logging.getLogger("mldev")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
logger.addHandler(handler)

LOG_INFO = logging.INFO
LOG_WARN = logging.WARN
LOG_ERROR = logging.ERROR
LOG_DEBUG = logging.DEBUG

__all__ = ["logger", "LOG_DEBUG", "LOG_INFO", "LOG_DEBUG"]