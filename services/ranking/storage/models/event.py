from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from services.ranking.storage.base import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    event_date = Column(DateTime, nullable=False)

    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=True)

    order = Column(Integer, nullable=False)

    game_version_id = Column(
        Integer,
        ForeignKey("game_versions.id"),
        nullable=False
    )

    event_type_id = Column(
        Integer,
        ForeignKey("event_types.id"),
        nullable=False
    )

    bracket_url = Column(String)
    playlist_url = Column(String)
