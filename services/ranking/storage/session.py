from sqlalchemy.orm import sessionmaker
from services.ranking.storage.engine import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
