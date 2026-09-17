from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.youtube.storage.base import Base
from services.youtube.storage import models  # noqa: F401

db_engine_name = "sqlite"
db_name = "yvm.db"  # YouTube Video Manager

DATABASE_URL = f"{db_engine_name}:///{db_name}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

Base.metadata.create_all(engine)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
