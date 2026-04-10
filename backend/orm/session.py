import os
import urllib.parse

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

db_user = os.getenv("DB_USER", "root")
db_password = os.getenv("DB_PASSWORD", "root")
db_host = os.getenv("DB_HOST", "localhost")
db_name = os.getenv("DB_NAME", "learnifydb")

db_password_encoded = urllib.parse.quote_plus(db_password)

DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    f"mysql+pymysql://{db_user}:{db_password_encoded}@{db_host}:3306/{db_name}",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
    future=True,
)


def get_session():
    """FastAPI dependency generator for SQLAlchemy Session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
