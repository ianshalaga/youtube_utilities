from sqlalchemy import create_engine

db_engine_name = "sqlite"
db_name = "sse.db"  # Seyfer Studios Events

DATABASE_URL = f"{db_engine_name}:///{db_name}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)
