from sqlalchemy import Column, Integer, String, ForeignKey
from services.ranking.storage.base import Base


class GameVersion(Base):
    __tablename__ = "game_versions"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    version = Column(String, nullable=False)
