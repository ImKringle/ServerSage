import logging
import sys

# Color codes for terminals (ANSI escape sequences)
RESET = "\x1b[0m"
COLOR_MAP = {
    logging.DEBUG: "\x1b[37m",    # White
    logging.INFO: "\x1b[32m",     # Green
    logging.WARNING: "\x1b[33m",  # Yellow
    logging.ERROR: "\x1b[31m",    # Red
    logging.CRITICAL: "\x1b[41m", # Red background
}

class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        if sys.stdout.isatty():
            color = COLOR_MAP.get(record.levelno, RESET)
            return f"{color}{message}{RESET}"
        else:
            return message

def setup_logger():
    logger = logging.getLogger("serversage")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logger()
