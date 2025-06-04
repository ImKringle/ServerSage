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
        color = COLOR_MAP.get(record.levelno, RESET)
        message = super().format(record)
        return f"{color}{message}{RESET}"

def setup_logger():
    logger = logging.getLogger("ServerSage")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = ColorFormatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = setup_logger()
