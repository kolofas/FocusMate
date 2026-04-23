from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin, schemas
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from focus.backend.database import models
from focus.backend.database.core import get_db
from focus.backend.settings import settings


class UserRead(schemas.BaseUser[int]):
    telegram_user_id: int | None = None


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class UserManager(IntegerIDMixin, BaseUserManager[models.WebUser, int]):
    reset_password_token_secret = settings.auth_jwt_secret
    verification_token_secret = settings.auth_jwt_secret

    async def on_after_register(
        self, user: models.WebUser, request: Request | None = None
    ) -> None:
        # Keep existing domain FKs on telegram_users by creating a paired row for web users.
        session = self.user_db.session

        web_user = await session.get(models.WebUser, user.id)
        if web_user is None or web_user.telegram_user_id is not None:
            return

        tg_user = models.TelegramUser(
            chat_id=f"web:{user.id}",
            username=user.email,
            first_name=None,
        )
        session.add(tg_user)
        await session.flush()

        web_user.telegram_user_id = tg_user.id
        await session.commit()


async def get_user_db(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[SQLAlchemyUserDatabase, None]:
    yield SQLAlchemyUserDatabase(session, models.WebUser)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy[models.WebUser, int]:
    return JWTStrategy(
        secret=settings.auth_jwt_secret,
        lifetime_seconds=settings.auth_jwt_lifetime_seconds,
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

fastapi_users = FastAPIUsers[models.WebUser, int](get_user_manager, [auth_backend])
current_active_user = fastapi_users.current_user(active=True)
current_active_user_optional = fastapi_users.current_user(optional=True, active=True)


def resolve_scope_user_id(
    current_user: models.WebUser | None,
    requested_user_id: int | None,
) -> int | None:
    if current_user is None:
        return requested_user_id
    if current_user.telegram_user_id is None:
        raise HTTPException(
            status_code=409,
            detail="User workspace is not initialized yet",
        )
    return current_user.telegram_user_id
