import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

log = logging.getLogger(__name__)

# ищем .env, поднимаясь от файла вверх
ENV_PATH = next(
    (p for p in Path(__file__).resolve().parents if (p / ".env").exists()), None
)
ENV_FILE = str(ENV_PATH / ".env") if ENV_PATH else None

# Небезопасный дефолт JWT-секрета: допустим в dev, запрещён в prod.
INSECURE_JWT_DEFAULT = "CHANGE_ME_DEV_ONLY"


class Settings(BaseSettings):
    database_url: str

    # окружение: "dev" | "prod". В "prod" небезопасная конфигурация валит старт.
    app_env: str = "dev"

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
    auth_jwt_secret: str = INSECURE_JWT_DEFAULT
    auth_jwt_lifetime_seconds: int = 60 * 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=ENV_PATH, extra="ignore")


settings = Settings()


def audit_security_config(cfg: Settings) -> list[str]:
    """Проверяет конфиг на небезопасные значения.

    Args:
        cfg: экземпляр настроек для проверки.

    Returns:
        Список сообщений о проблемах (пустой список — проблем нет).
    """
    issues: list[str] = []
    if cfg.auth_jwt_secret == INSECURE_JWT_DEFAULT:
        issues.append(
            "AUTH_JWT_SECRET использует небезопасный дефолт — задайте свой секрет"
        )
    origins = [o.strip() for o in cfg.web_cors_origins.split(",") if o.strip()]
    if not origins:
        issues.append(
            "WEB_CORS_ORIGINS пуст — CORS откроется для всех источников (allow_origins=*)"
        )
    return issues


def enforce_security_config(cfg: Settings) -> None:
    """Применяет политику безопасности конфига.

    В prod (`app_env == "prod"`) при любой найденной проблеме останавливает старт
    исключением. В остальных окружениях проблемы только логируются как warning.

    Args:
        cfg: экземпляр настроек для проверки.

    Raises:
        RuntimeError: если `app_env == "prod"` и найдена хотя бы одна проблема.
    """
    issues = audit_security_config(cfg)
    if not issues:
        return
    if cfg.app_env == "prod":
        raise RuntimeError("Небезопасная конфигурация в prod: " + "; ".join(issues))
    for msg in issues:
        log.warning("config: %s", msg)
