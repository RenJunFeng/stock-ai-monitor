from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


settings = get_settings()

if settings.database_url.startswith("sqlite:///"):
    sqlite_path = settings.database_url.replace("sqlite:///", "", 1)
    database_file = Path(sqlite_path)
    if not database_file.is_absolute():
        database_file = Path.cwd() / database_file
    database_file.parent.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_runtime_schema() -> None:
    """Apply tiny SQLite-safe upgrades for installations without migrations."""
    inspector = inspect(engine)
    if "watchlist_stocks" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("watchlist_stocks")}
    if "group_name" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE watchlist_stocks ADD COLUMN group_name VARCHAR(80) DEFAULT '默认分组'"))
            connection.execute(text("UPDATE watchlist_stocks SET group_name = '默认分组' WHERE group_name IS NULL OR group_name = ''"))
