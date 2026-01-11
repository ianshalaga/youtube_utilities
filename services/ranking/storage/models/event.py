from sqlalchemy import Column, Integer, String, ForeignKey
from services.ranking.storage.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"))
    game_id = Column(Integer, ForeignKey("games.id"))
    bracket_url = Column(String)
    playlist_url = Column(String)
