import asyncio
from helper.logger import logger
from .input_handler import prompt_input

console_stop_event = asyncio.Event()

async def ainput(prompt: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: prompt_input(prompt))

def _get_section_key(path: str):
    """Split path like 'discord.control_channel' into ('discord', 'control_channel')."""
    parts = path.split(".")
    if len(parts) != 2:
        raise ValueError("Path must be in format <section>.<key>")
    return parts[0], parts[1]

async def reset_config(config):
    print("Are you sure you want to RESET the entire config? Type YES to confirm:")
    confirm = await ainput("> ")
    if confirm == "YES":
        config.clear_all()
        config.save()
        print("Config database reset!")
        logger.info("Config DB reset via console.")
    else:
        print("Reset cancelled.")

async def update_config_entry(config, path: str, value: str):
    try:
        section, key = _get_section_key(path)
    except ValueError as e:
        print(str(e))
        return

    section_data = config.get_section(section)
    if section_data is None:
        print(f"Section '{section}' does not exist.")
        return
    if key not in section_data:
        print(f"Key '{key}' does not exist in section '{section}'.")
        return

    config.set(section, key, value)
    config.save()
    print(f"Updated [{section}] {key} = {value}")
    logger.info(f"Config updated via console: [{section}] {key} = {value}")

async def list_config_section(config, section: str):
    section_data = config.get_section(section)
    if section_data is None:
        print(f"Section '{section}' does not exist.")
        return
    print(f"\n[{section}]")
    for key, value in section_data.items():
        print(f"{key} = {value}")
    print("")

async def run_console_loop(config, shutdown_func=None):
    print("Config Console started. Commands:\n - reset\n - update <section.key> <value>\n - list [<section>]\n - exit\n")
    try:
        while not console_stop_event.is_set():
            try:
                cmdline = await ainput("> ")
            except asyncio.CancelledError:
                break
            if not cmdline.strip():
                continue
            args = cmdline.split(maxsplit=2)
            command = args[0].lower()

            if command == "exit":
                print("Exiting console...")
                console_stop_event.set()
                if shutdown_func:
                    await shutdown_func()
                break
            elif command == "reset":
                await reset_config(config)
            elif command == "update":
                if len(args) < 3:
                    print("Usage: update <section.key> <value>")
                    continue
                await update_config_entry(config, args[1], args[2])
            elif command == "list":
                if len(args) < 2:
                    # No section specified, print entire config
                    all_sections = config.all()
                    if not all_sections:
                        print("Config is empty.")
                        continue
                    for section, data in all_sections.items():
                        print(f"\n[{section}]")
                        for key, value in data.items():
                            print(f"{key} = {value}")
                    print("")
                else:
                    await list_config_section(config, args[1])
            else:
                print("Unknown command. Valid commands: reset, update, list, exit")
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt detected, exiting console...")
        console_stop_event.set()
        if shutdown_func:
            await shutdown_func()