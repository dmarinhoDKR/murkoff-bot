import discord
from discord import app_commands
from discord.ext import commands

from config import settings
from database import RegistroRepository


def criar_embed_pendente(
    *,
    registro_id: int,
    member_id: int,
    nota: str,
    morreu: bool,
    experimento: str,
    dificuldade: str,
    incapacitacoes: int,
    observacao: str | None,
) -> discord.Embed:
    embed = discord.Embed(
        title=(f"📋 REGISTRO CLÍNICO PENDENTE — #{registro_id:06d}"),
        color=discord.Color.from_rgb(196, 145, 45),
    )

    embed.add_field(
        name="Reagente",
        value=f"<@{member_id}>",
        inline=True,
    )
    embed.add_field(
        name="Nota",
        value=nota,
        inline=True,
    )
    embed.add_field(
        name="Morreu",
        value="Sim" if morreu else "Não",
        inline=True,
    )
    embed.add_field(
        name="Experimento",
        value=experimento,
        inline=False,
    )
    embed.add_field(
        name="Dificuldade",
        value=dificuldade,
        inline=True,
    )
    embed.add_field(
        name="Incapacitações",
        value=str(incapacitacoes),
        inline=True,
    )

    if observacao:
        embed.add_field(
            name="Observação",
            value=observacao,
            inline=False,
        )

    embed.add_field(
        name="Estado",
        value="⏳ Aguardando avaliação do diretor",
        inline=False,
    )

    embed.set_footer(
        text=("Fonte: formulário manual • Ainda não incluído nas estatísticas")
    )

    return embed


class RegistroModal(
    discord.ui.Modal,
    title="Registro clínico do experimento",
):
    experimento = discord.ui.TextInput(
        label="Experimento",
        placeholder="Ex.: Kill the Snitch",
        min_length=2,
        max_length=100,
    )

    dificuldade = discord.ui.TextInput(
        label="Dificuldade",
        placeholder="Ex.: Psicocirurgia",
        min_length=2,
        max_length=50,
    )

    incapacitacoes = discord.ui.TextInput(
        label="Número de incapacitações",
        placeholder="Digite 0 se não caiu",
        default="0",
        min_length=1,
        max_length=2,
    )

    observacao = discord.ui.TextInput(
        label="Observação opcional",
        placeholder="Informações adicionais sobre a partida",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=500,
    )

    def __init__(
        self,
        *,
        bot: commands.Bot,
        repository: RegistroRepository,
        nota: str,
        morreu: bool,
    ) -> None:
        super().__init__()

        self.bot = bot
        self.repository = repository
        self.nota = nota
        self.morreu = morreu

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "⛔ Este formulário só pode ser usado no servidor.",
                ephemeral=True,
            )
            return

        try:
            incapacitacoes = int(str(self.incapacitacoes.value).strip())
        except ValueError:
            await interaction.response.send_message(
                "⚠️ Incapacitações deve ser um número inteiro.",
                ephemeral=True,
            )
            return

        if incapacitacoes < 0 or incapacitacoes > 99:
            await interaction.response.send_message(
                "⚠️ Incapacitações deve estar entre 0 e 99.",
                ephemeral=True,
            )
            return

        observacao = str(self.observacao.value).strip() or None

        registro_id = await self.repository.criar(
            guild_id=interaction.guild.id,
            member_id=interaction.user.id,
            submitted_by=interaction.user.id,
            source="manual",
            experimento=str(self.experimento.value),
            dificuldade=str(self.dificuldade.value),
            nota=self.nota,
            incapacitacoes=incapacitacoes,
            morreu=self.morreu,
            observacao=observacao,
        )

        channel = self.bot.get_channel(settings.discord_validation_channel_id)

        if channel is None:
            try:
                channel = await self.bot.fetch_channel(
                    settings.discord_validation_channel_id
                )
            except discord.DiscordException:
                channel = None

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                (
                    "⚠️ O registro foi salvo, mas o canal de "
                    "validação não foi encontrado. Informe o dono."
                ),
                ephemeral=True,
            )
            return

        embed = criar_embed_pendente(
            registro_id=registro_id,
            member_id=interaction.user.id,
            nota=self.nota,
            morreu=self.morreu,
            experimento=str(self.experimento.value),
            dificuldade=str(self.dificuldade.value),
            incapacitacoes=incapacitacoes,
            observacao=observacao,
        )

        validation_message = await channel.send(
            embed=embed,
        )

        await self.repository.salvar_mensagem_validacao(
            registro_id=registro_id,
            guild_id=interaction.guild.id,
            channel_id=channel.id,
            message_id=validation_message.id,
        )

        await interaction.response.send_message(
            (
                f"✅ Registro #{registro_id:06d} enviado para "
                "avaliação do diretor.\n"
                "Ele ainda não foi incluído nas estatísticas."
            ),
            ephemeral=True,
        )


class RegistrosCog(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
        repository: RegistroRepository,
    ) -> None:
        self.bot = bot
        self.repository = repository

    @app_commands.command(
        name="registrar",
        description="Envia o resultado de um experimento para validação.",
    )
    @app_commands.describe(
        nota="Nota obtida no experimento",
        morreu="Indica se o reagente morreu durante o experimento",
    )
    @app_commands.choices(
        nota=[
            app_commands.Choice(name="A+", value="A+"),
            app_commands.Choice(name="A", value="A"),
            app_commands.Choice(name="A-", value="A-"),
            app_commands.Choice(name="B+", value="B+"),
            app_commands.Choice(name="B", value="B"),
            app_commands.Choice(name="B-", value="B-"),
            app_commands.Choice(name="C+", value="C+"),
            app_commands.Choice(name="C", value="C"),
            app_commands.Choice(name="C-", value="C-"),
            app_commands.Choice(name="D+", value="D+"),
            app_commands.Choice(name="D", value="D"),
            app_commands.Choice(name="D-", value="D-"),
            app_commands.Choice(name="F", value="F"),
        ]
    )
    async def registrar(
        self,
        interaction: discord.Interaction,
        nota: app_commands.Choice[str],
        morreu: bool,
    ) -> None:
        modal = RegistroModal(
            bot=self.bot,
            repository=self.repository,
            nota=nota.value,
            morreu=morreu,
        )

        await interaction.response.send_modal(modal)
