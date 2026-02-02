from sqlalchemy import Column, Integer, ForeignKey, String, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Duel(Base, WithCode):
    __tablename__ = "duels"

    # Indexes
    __table_args__ = (
        Index("ix_duels_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    duel_type_id = Column(Integer, ForeignKey("duel_types.id"), nullable=False)

    # Properties
    order = Column(Integer, nullable=False)
    video_url = Column(String, nullable=True)

    # Relationships
    event = relationship("Event")
    duel_type = relationship("DuelType")
