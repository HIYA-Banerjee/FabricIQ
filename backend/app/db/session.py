# pyrefly: ignore [missing-import]
from sqlalchemy import create_engine  # pyrefly: ignore [missing-import]
from sqlalchemy.orm import sessionmaker, declarative_base  # pyrefly: ignore [missing-import]
from app.core.config import settings

# If sqlite is used, we need check_same_thread=False
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
