from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Event(Base, WithCode):
    __tablename__ = "events"

    # Indexes
    __table_args__ = (
        Index("ix_events_code", "code"),
        Index("ix_events_season_id", "season_id"),
        Index("ix_events_game_version_platform_id", "game_version_platform_id"),
    )

    id = Column(Integer, primary_key=True)

    # FKs
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=True)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=False)
    event_type_id = Column(
        Integer,
        ForeignKey("event_types.id"),
        nullable=False
    )
    game_version_platform_id = Column(
        Integer,
        ForeignKey("game_version_platforms.id"),
        nullable=False
    )

    # Fields
    name = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    order = Column(Integer, nullable=False)
    bracket_url = Column(String, nullable=True)
    playlist_url = Column(String, nullable=True)

    # Relationships
    season = relationship("Season")
    event_type = relationship("EventType")
    region = relationship("Region")
    game_version_platform = relationship("GameVersionPlatform")
