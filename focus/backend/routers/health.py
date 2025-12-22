from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
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
def db_status(db: Session = Depends(get_db)):
    counts = {}
    for table in {"tasks", "inbox_events", "focus_list", "focus_items"}:
        try:
            counts[table] = (
                db.execute(text(f'SELECT COUNT(*) FROM "{table}"')).scalar() or 0
            )
        except Exception:
            counts[table] = None

    version = db.execute(text("SELECT version()")).scalar()
    alembic_ver = db.execute(text("SELECT version_num FROM alembic_version")).scalar()

    return {
        "database_url": _mask_url(str(engine.url)),
        "alembic_version": alembic_ver,
        "tables": counts,
        "pg_version": version,
    }
