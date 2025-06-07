from discord import Embed, Color
from discord.ext import commands
from helper.logger import logger

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.control_channel = bot.control_channel

    @commands.command(name="help")
    async def help_command(self, ctx):
        if str(ctx.channel.id) != str(self.control_channel):
            await ctx.send("⚠️ ServerSage Commands can only be used in the designated control channel.")
            return
        embed = Embed(
            title="🧙 ServerSage Command Chamber 🖥️",
            description="Here’s a list of all available commands:\n",
            color=Color.teal()
        )
        field_chunks = []
        current_chunk = ""
        for command in self.bot.commands:
            if command.hidden:
                continue
            usage = f"!{command.name} {command.signature}".strip()
            help_text = (command.help or "(No description)").strip()
            entry = f"{usage}\n - {help_text}\n\n"
            if len(current_chunk) + len(entry) > 950:
                field_chunks.append(current_chunk)
                current_chunk = ""
            current_chunk += entry
        if current_chunk:
            field_chunks.append(current_chunk)
        for i, chunk in enumerate(field_chunks):
            embed.add_field(name=f"Command Reference {i + 1}", value=f"```{chunk}```", inline=False)

        embed.set_footer(
            text="⚠️ Double-check the server index before issuing any commands!\n— ServerSage, your digital server wizard 🧙‍♂️"
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
