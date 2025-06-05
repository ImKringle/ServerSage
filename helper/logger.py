import logging
import sys
import os
import shutil
from datetime import datetime

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
    log_filename = "ServerSage.log"

    if os.path.exists(log_filename):
        os.makedirs("Logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_name = os.path.join("Logs", f"ServerSage_{timestamp}.log")
        shutil.move(log_filename, new_name)

    logger = logging.getLogger("serversage")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColorFormatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(log_filename)
    file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger

def print_colored(msg, level=logging.INFO):
    print(f"{COLOR_MAP.get(level, RESET)}{msg}{RESET}")

logger = setup_logger()
