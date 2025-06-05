import sys
import os
from helper.logger import logger

def prompt_input(prompt, env_var=None, default=None):
    """
    Prompt the user for input via stdin, optionally falling back to an environment variable or a default value.
    Parameters:
    - prompt (str): The message shown to the user when asking for input.
    - env_var (str, optional): The name of an environment variable to check before prompting. If set and exists, its value is returned.
    - default (str, optional): The value to return if input is interrupted or empty.
    Returns:
    - str: The input value from the environment variable, user prompt, or default.
    Exits the program if input is interrupted and no default is provided.
    """
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