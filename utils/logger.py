"""
结构化日志 — 双通道输出（控制台 + 文件）。
控制台输出自动过滤非 ASCII 字符以兼容 Windows GBK。
"""
import logging
import sys
import re

_logger = None
_EMOJI_RE = re.compile(
    "[\U0001f300-\U0001f9ff\U0001fa00-\U0001ffff\u2600-\u27BF\u2B50\u2702-\u27B0\u24C2-\U0001f251"
    "\U0001f000-\U0001f02f\U0001f0a0-\U0001f0ff\U0001f100-\U0001f64f\U0001f680-\U0001f6ff"
    "\U0001f780-\U0001f7ff\U0001f800-\U0001f8ff\U0001f900-\U0001f9ff\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff\U0001fb00-\U0001fbff\U0001fc00-\U0001fcff\U0001fd00-\U0001fdff"
    "\U0001fe00-\U0001feff\U0001ff00-\U0001ffff\U00010000-\U0010ffff]+"
)


class _SafeConsoleHandler(logging.StreamHandler):
    """Windows 兼容控制台 Handler — 自动剥离 emoji 和不可编码字符"""

    def emit(self, record):
        try:
            msg = self.format(record)
            clean = _EMOJI_RE.sub("[*]", msg)
            stream = self.stream
            stream.write(clean + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


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
    console = _SafeConsoleHandler(sys.stdout)
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
