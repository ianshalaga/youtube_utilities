from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
