import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from database import Database, RegistroRepository

from cogs.registros import RegistrosCog


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("terminal_murkoff")

database = Database(
    database_path=settings.database_path,
    schema_path=(Path(__file__).resolve().parent / "database" / "schema.sql"),
)

registro_repository = RegistroRepository(database)


class TerminalMurkoff(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self) -> None:
        await database.initialize()

        logger.info(
            "Banco de dados inicializado em %s.",
            settings.database_path,
        )

        await self.add_cog(
            RegistrosCog(
                bot=self,
                repository=registro_repository,
            )
        )

        guild = discord.Object(
            id=settings.discord_guild_id,
        )

        # Copia os comandos globais para o servidor de desenvolvimento.
        # Isso faz os comandos aparecerem quase imediatamente.
        self.tree.copy_global_to(guild=guild)

        comandos = await self.tree.sync(guild=guild)

        logger.info(
            "%s comando(s) sincronizado(s) no servidor %s.",
            len(comandos),
            settings.discord_guild_id,
        )


bot = TerminalMurkoff()


@bot.event
async def on_ready() -> None:
    if bot.user is None:
        return

    logger.info(
        "Terminal conectado como %s (%s).",
        bot.user,
        bot.user.id,
    )

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="os experimentos",
        )
    )


@bot.tree.command(
    name="status",
    description="Verifica o estado operacional do Terminal Murkoff.",
)
async def status(
    interaction: discord.Interaction,
) -> None:
    embed = discord.Embed(
        title="🟢 TERMINAL OPERACIONAL",
        description=(
            "Conexão com a instalação estabelecida.\n"
            "O programa está aceitando novos registros clínicos."
        ),
        color=discord.Color.from_rgb(45, 124, 103),
    )

    embed.add_field(
        name="Reagente",
        value=interaction.user.mention,
        inline=True,
    )
    embed.add_field(
        name="Latência",
        value=f"{round(bot.latency * 1000)} ms",
        inline=True,
    )
    embed.set_footer(text=("Terminal Murkoff • Programa experimental não oficial"))

    await interaction.response.send_message(
        embed=embed,
    )


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    logger.exception(
        "Erro durante comando de aplicação",
        exc_info=error,
    )

    mensagem = "⚠️ O terminal encontrou uma inconsistência durante o processamento."

    if interaction.response.is_done():
        await interaction.followup.send(
            mensagem,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            mensagem,
            ephemeral=True,
        )


if __name__ == "__main__":
    bot.run(
        settings.discord_token,
        log_handler=None,
    )
