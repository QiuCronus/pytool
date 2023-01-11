import functools
import os
import sys

from loguru._colorizer import Colorizer
from loguru._logger import Core, Logger, Level

__all__ = ["getLogger", "getFileLogger", "setLevel"]

LOG_FORMAT = "{time:YYYY/MM/DD HH:mm:ss.SS} [{level: <8}] {module}.{function}[{line}]: {message}"
sys.tracebacklimit = 2

DEBUG = "DEBUG"
INFO = "INFO"
WARNING = "WARNING"
ERROR = "ERROR"


@functools.lru_cache(maxsize=10)
def getLogger(module, level=INFO):
    # type: (str, str) -> Logger
    _log = Logger(
        core=Core(),
        exception=None,
        depth=0,
        record=False,
        lazy=False,
        colors=False,
        raw=False,
        capture=True,
        patcher=None,
        extra={},
    )
    _log.remove()
    _log.add(sys.stdout, level=level, format=LOG_FORMAT, backtrace=True)
    return _log


@functools.lru_cache(maxsize=None)
def getFileLogger(module):
    # type: (str) -> Logger
    mod = module.replace(".", os.sep)
    _log = Logger(
        core=Core(),
        exception=None,
        depth=0,
        record=False,
        lazy=False,
        colors=False,
        raw=False,
        capture=True,
        patcher=None,
        extra={},
    )
    _log.remove()

    log_dirs = os.path.join(os.getcwd(), "data", "logs", mod)
    if not os.path.exists(log_dirs):
        os.makedirs(log_dirs)
    log_path = os.path.join(log_dirs, "{time:YYYY-MM-DD}.log")
    _log.add(
        log_path,
        level=DEBUG,
        format=LOG_FORMAT,
        backtrace=True,
        rotation="00:00",
        retention=0,
        encoding="utf8",
    )
    return _log


def setLevel(logger, level_name):
    # type: (Logger, str) -> None
    _, nu, color, icon = logger.level(level_name)
    ansi = Colorizer.ansify(color)
    level = Level(level_name, nu, color, icon)
    with logger._core.lock:
        logger._core.min_level = nu
        logger._core.levels[level_name] = level
        logger._core.levels_ansi_codes[level_name] = ansi
        for handler in logger._core.handlers.values():
            if level_name == "DEBUG":
                handler._exception_formatter._backtrace = True
            handler._levelno = nu
