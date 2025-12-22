from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..settings import settings

engine = create_engine(
    settings.database_url,
    future=True,
    echo=settings.sql_echo,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
