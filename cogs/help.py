from discord.ext import commands
from helper.logger import logger

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.control_channel = bot.config.get("discord", {}).get("control_channel") or bot.control_channel
        if not self.control_channel:
            raise logger.critical("Control channel not configured anywhere! Startup will fail!")

    @commands.command(name="help")
    async def help_command(self, ctx):
        """
        Shows the help menu with available commands and usage.
        """
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send(f"⚠️ ServerSage Commands can only be used in the designated control channel. Ask someone with permission!")
            return
        description = "**:mage: Welcome to ServerSage Command Chamber :desktop:**\n\n"
        description += "### :wrench: Available Commands\n\n```\n"
        for command in self.bot.commands:
            if not command.hidden:
                usage = f"!{command.name} {command.signature}".strip()
                help_text = (command.help or "").strip()
                if help_text:
                    description += f"{usage:<25} → {help_text}\n"
                else:
                    description += f"{usage}\n"
        description += "```\n"
        description += (
            ":warning: **Please double-check the server index** before issuing any commands.\n"
            "If you're unsure about anything, ask first. Let’s keep my servers stable, thanks :shield:\n"
            "— *ServerSage, your digital server wizard*"
        )
        await ctx.send(description)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))