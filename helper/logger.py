import logging
from logging import handlers
import sys
import os
import shutil
from datetime import datetime

RESET = "\x1b[0m"  # No color (Reset)
COLOR_MAP = {
    logging.DEBUG: "\x1b[37m",    # White
    logging.INFO: "\x1b[32m",     # Green
    logging.WARNING: "\x1b[33m",  # Yellow
    logging.ERROR: "\x1b[31m",    # Red
    logging.CRITICAL: "\x1b[41m", # Red background
}

MAX_LOG_DIR_SIZE_MB = 100
MAX_LOG_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB max per log file
BACKUP_COUNT = 10  # Keep up to 10 rotated files

LOG_DIR = "logs"
LOG_FILENAME = os.path.join(LOG_DIR, "ServerSage.log")

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

def print_colored(msg, level=logging.INFO):
    print(f"{COLOR_MAP.get(level, RESET)}{msg}{RESET}")

class TimestampedRotatingFileHandler(handlers.RotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dirname, basename = os.path.split(self.baseFilename)
        filename_root, ext = os.path.splitext(basename)
        new_name = os.path.join(dirname, f"{filename_root}-{timestamp}{ext}")

        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, new_name)

        if self.backupCount > 0:
            files = sorted(
                f for f in os.listdir(dirname)
                if f.startswith(filename_root) and f.endswith(ext) and f != basename
            )
            files.sort(key=lambda f: os.path.getmtime(os.path.join(dirname, f)), reverse=True)

            for old_file in files[self.backupCount:]:
                try:
                    os.remove(os.path.join(dirname, old_file))
                except Exception:
                    pass
        self.mode = 'a'
        self.stream = self._open()

def setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)

    dir_size_bytes = get_directory_size(LOG_DIR)
    if dir_size_bytes > MAX_LOG_DIR_SIZE_MB * 1024 * 1024:
        clear_directory(LOG_DIR)

    logger = logging.getLogger("serversage")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = ColorFormatter('[%(asctime)s] [%(levelname)s] %(message)s', "%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    file_handler = TimestampedRotatingFileHandler(
        LOG_FILENAME,
        maxBytes=MAX_LOG_FILE_SIZE_BYTES,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(file_formatter)

    if os.path.exists(LOG_FILENAME) and os.path.getsize(LOG_FILENAME) > 0:
        file_handler.doRollover()

    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
