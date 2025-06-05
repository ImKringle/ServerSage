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

MAX_LOG_DIR_SIZE_MB = 100
LOG_DIR = "Logs"

class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        if sys.stdout.isatty():
            color = COLOR_MAP.get(record.levelno, RESET)
            return f"{color}{message}{RESET}"
        else:
            return message

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if os.path.isfile(filepath):
                total_size += os.path.getsize(filepath)
    return total_size

def clear_directory(directory):
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        try:
            if os.path.isfile(filepath) or os.path.islink(filepath):
                os.unlink(filepath)
            elif os.path.isdir(filepath):
                shutil.rmtree(filepath)
        except Exception as e:
            print_colored(f"Failed to delete {filepath}: {e}", logging.ERROR)

def setup_logger():
    log_filename = "ServerSage.log"

    os.makedirs(LOG_DIR, exist_ok=True)

    dir_size_bytes = get_directory_size(LOG_DIR)
    if dir_size_bytes > MAX_LOG_DIR_SIZE_MB * 1024 * 1024:
        clear_directory(LOG_DIR)

    if os.path.exists(log_filename):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_name = os.path.join(LOG_DIR, f"ServerSage_{timestamp}.log")
        shutil.move(log_filename, new_name)

    logger = logging.getLogger("serversage")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColorFormatter('[%(asctime)s] [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
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
