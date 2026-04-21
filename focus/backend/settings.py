from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# ищем .env, поднимаясь от файла вверх
ENV_PATH = next(
    (p for p in Path(__file__).resolve().parents if (p / ".env").exists()), None
)
ENV_FILE = str(ENV_PATH / ".env") if ENV_PATH else None


class Settings(BaseSettings):
    database_url: str

    inbox_dedup_minutes: int = 10

    max_description_length: int = 4000
    max_title_length: int = 300

    urgent_tag: str = "urgent"
    focus_limit: int = 5
    app_timezone: str = "Europe/Amsterdam"
    reminders_worker_enabled: bool = True
    reminders_poll_seconds: int = 30
    reminders_batch_size: int = 50

    log_level: str = "INFO"  # DEBUG/INFO/WARN/ERROR
    sql_echo: bool = False  # Печать SQL запросов

    # telegram
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str | None = None  # для пути /telegram/webhook/{secret}
    telegram_mode: str = "webhook"  # "webhook" | "polling"
    telegram_log_updates: bool = True
    web_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auth_jwt_secret: str = "CHANGE_ME_DEV_ONLY"
    auth_jwt_lifetime_seconds: int = 60 * 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


settings = Settings()
