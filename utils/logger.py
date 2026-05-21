import logging
import sys

_logger = None


def get_logger(name: str = "minest"):
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)
    _logger.handlers.clear()

    fmt_console = logging.Formatter(
        "%(asctime)s [%(levelname)-5s] %(message)s", datefmt="%H:%M:%S"
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt_console)
    _logger.addHandler(console)

    try:
        fmt_file = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d %(message)s"
        )
        file_handler = logging.FileHandler("minest.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt_file)
        _logger.addHandler(file_handler)
    except OSError:
        pass

    return _logger


logger = get_logger()
