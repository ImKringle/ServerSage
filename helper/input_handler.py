import sys
import os
from helper.logger import logger

def prompt_input(prompt, env_var=None, default=None):
    if env_var and os.getenv(env_var):
        logger.info(f"{prompt} (from ${env_var})")
        return os.getenv(env_var)

    try:
        sys.stdout.write(f"{prompt}\n> ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        if not line:
            raise EOFError
        return line.strip() or default
    except (KeyboardInterrupt, EOFError):
        logger.warning("Input interrupted or unavailable.")
        if default is not None:
            logger.info(f"Using default value: {default}")
            return default
        sys.exit(1)