import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    discord_token: str
    discord_guild_id: int
    discord_validation_channel_id: int
    database_path: Path


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
    validation_channel_id = os.getenv(
        "DISCORD_VALIDATION_CHANNEL_ID",
        "",
    ).strip()
    database_path = os.getenv(
        "DATABASE_PATH",
        "data/murkoff.db",
    ).strip()

    if not token:
        raise RuntimeError("DISCORD_TOKEN não foi configurado no .env.")

    if not guild_id.isdigit():
        raise RuntimeError(
            "DISCORD_GUILD_ID deve conter somente o ID numérico do servidor."
        )

    if not validation_channel_id.isdigit():
        raise RuntimeError(
            "DISCORD_VALIDATION_CHANNEL_ID deve conter o ID numérico "
            "do canal de validação."
        )

    return Settings(
        discord_token=token,
        discord_guild_id=int(guild_id),
        discord_validation_channel_id=int(validation_channel_id),
        database_path=BASE_DIR / database_path,
    )


settings = load_settings()
