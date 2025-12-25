from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.core import engine, get_db


router = APIRouter()


@router.get("/ping")
def ping():
    return {"status": "ok"}


def _mask_url(url_str: str) -> str:
    from sqlalchemy.engine.url import make_url

    u = make_url(url_str)
    if u.password:
        u = u.set(password="***")
    return str(u)


@router.get("/db")
async def db_status(db: AsyncSession = Depends(get_db)):
    counts: dict[str, int | None] = {}

    for table in ("tasks", "inbox_events", "focus_list", "focus_items"):
        try:
            result = await db.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
            counts[table] = result.scalar() or 0
        except Exception:
            counts[table] = None

    version_result = await db.execute(text("SELECT version()"))
    version = version_result.scalar()

    alembic_result = await db.execute(text("SELECT version_num FROM alembic_version"))
    alembic_ver = alembic_result.scalar()

    return {
        "database_url": _mask_url(str(engine.url)),
        "alembic_version": alembic_ver,
        "tables": counts,
        "pg_version": version,
    }
