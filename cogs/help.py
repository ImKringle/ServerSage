import discord
from helper.logger import logger
from discord import Embed, Color
from discord.ext import commands
from discord import app_commands

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.control_channel = bot.control_channel

    @app_commands.command(name="help", description="Display the list of available slash commands")
    async def slash_help_command(self, interaction: discord.Interaction):
        if str(interaction.channel.id) != str(self.control_channel):
            await interaction.response.send_message(
                "⚠️ ServerSage Commands can only be used in the designated control channel.",
                ephemeral=True
            )
            return
        embed = self._generate_help_embed()
        await interaction.response.send_message(embed=embed)
    def _format_command(self, command, parent_name="") -> list[str]:
        """
        Recursively format a command and its subcommands into a list of strings.
        """
        full_name = f"/{parent_name} {command.name}".strip()
        try:
            params = " ".join(f"<{opt.name}>" for opt in getattr(command, "options", []) if opt.name)
        except Exception as e:
            logger.warning("Failed to get options for command '%s': %s", full_name, e)
            params = ""
        usage = f"{full_name} {params}".strip()
        description = command.description or "(No description)"
        lines = [f"{usage}\n - {description}\n"]
        if hasattr(command, "commands") and command.commands:
            for subcmd in command.commands:
                lines.extend(self._format_command(subcmd, parent_name=f"{parent_name} {command.name}".strip()))
        return lines

    def _generate_help_embed(self) -> Embed:
        embed = Embed(
            title="🧙 ServerSage Slash Commands 🖥️",
            description="Here’s a list of all available slash commands:\n",
            color=Color.teal()
        )
        all_entries = []
        for cmd in self.bot.tree.walk_commands():
            if getattr(cmd, "hidden", False):
                continue
            all_entries.extend(self._format_command(cmd))

        field_chunks = []
        current_chunk = ""
        for entry in all_entries:
            if len(current_chunk) + len(entry) > 950:
                field_chunks.append(current_chunk)
                current_chunk = entry
            else:
                current_chunk += entry
        if current_chunk:
            field_chunks.append(current_chunk)

        for i, chunk in enumerate(field_chunks):
            embed.add_field(name=f"Slash Command Reference {i + 1}", value=f"```{chunk}```", inline=False)

        embed.set_footer(
            text="⚠️ Use commands responsibly!\n— ServerSage, your digital server wizard 🧙‍♂️"
        )
        return embed

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))