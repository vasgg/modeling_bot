import logging.config
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = (
    "%(asctime)s.%(msecs)03d [%(levelname)8s] "
    "[%(module)s:%(funcName)s:%(lineno)d] %(message)s"
)
LOG_DATEFMT = "%d.%m.%Y %H:%M:%S%z"


def setup_logs(app_name: str) -> None:
    Path("logs").mkdir(parents=True, exist_ok=True)
    logging.config.dictConfig(get_logging_config(app_name))


def get_logging_config(app_name: str) -> dict:
    file_handler = {
        "()": RotatingFileHandler,
        "formatter": "main",
        "maxBytes": 5_000_000,
        "backupCount": 3,
        "encoding": "utf-8",
    }
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"main": {"format": LOG_FORMAT, "datefmt": LOG_DATEFMT}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "main",
                "stream": sys.stdout,
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "main",
                "stream": sys.stderr,
            },
            "file_info": {
                **file_handler,
                "level": "INFO",
                "filename": f"logs/{app_name}.log",
            },
            "file_debug": {
                **file_handler,
                "level": "DEBUG",
                "filename": f"logs/{app_name}_debug.log",
            },
        },
        "loggers": {
            "root": {
                "level": "DEBUG",
                "handlers": ["stdout", "stderr", "file_info", "file_debug"],
            }
        },
    }
