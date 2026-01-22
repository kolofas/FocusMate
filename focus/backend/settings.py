from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# ищем .env, поднимаясь от файла вверх
ENV_PATH = next((p for p in Path(__file__).resolve().parents if (p / ".env").exists()), None)
ENV_FILE = str(ENV_PATH / ".env") if ENV_PATH else None


class Settings(BaseSettings):
    database_url: str

    inbox_dedup_minutes: int = 10

    max_description_length: int = 4000
    max_title_length: int = 300

    urgent_tag: str = "urgent"
    focus_limit: int = 5

    log_level: str = "INFO"  # DEBUG/INFO/WARN/ERROR
    sql_echo: bool = False  # Печать SQL запросов

    # telegram
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None  # для пути /telegram/webhook/{secret}
    telegram_mode: str = "webhook"  # "webhook" | "polling"
    telegram_log_updates: bool = True

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


settings = Settings()
