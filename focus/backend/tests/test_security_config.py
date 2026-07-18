from __future__ import annotations

import pytest

from focus.backend.settings import (
    INSECURE_JWT_DEFAULT,
    Settings,
    audit_security_config,
    enforce_security_config,
)


def _make_settings(**overrides: object) -> Settings:
    """Строит Settings с безопасными значениями по умолчанию для теста.

    Args:
        **overrides: поля, которые нужно переопределить.

    Returns:
        Экземпляр Settings (без обращения к БД — поля просто строки/числа).
    """
    base: dict[str, object] = {
        "database_url": "postgresql+asyncpg://u:p@localhost:5432/db",
        "auth_jwt_secret": "a" * 64,
        "web_cors_origins": "https://api.focus-mate.ru",
        "app_env": "dev",
    }
    base.update(overrides)
    return Settings(**base)


def test_audit_flags_default_jwt_secret():
    issues = audit_security_config(_make_settings(auth_jwt_secret=INSECURE_JWT_DEFAULT))
    assert any("AUTH_JWT_SECRET" in msg for msg in issues)


def test_audit_flags_empty_cors():
    issues = audit_security_config(_make_settings(web_cors_origins="  , "))
    assert any("WEB_CORS_ORIGINS" in msg for msg in issues)


def test_audit_clean_when_secure():
    assert audit_security_config(_make_settings()) == []


def test_enforce_raises_in_prod_on_default_secret():
    cfg = _make_settings(app_env="prod", auth_jwt_secret=INSECURE_JWT_DEFAULT)
    with pytest.raises(RuntimeError):
        enforce_security_config(cfg)


def test_enforce_raises_in_prod_on_empty_cors():
    cfg = _make_settings(app_env="prod", web_cors_origins="")
    with pytest.raises(RuntimeError):
        enforce_security_config(cfg)


def test_enforce_does_not_raise_in_dev_on_default_secret():
    cfg = _make_settings(app_env="dev", auth_jwt_secret=INSECURE_JWT_DEFAULT)
    enforce_security_config(cfg)  # dev: только warning, без исключения


def test_enforce_does_not_raise_in_prod_when_secure():
    enforce_security_config(_make_settings(app_env="prod"))
