from sqlalchemy import Column, Integer, ForeignKey, String, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Duel(Base, WithCode):
    __tablename__ = "duels"

    # Indexes
    __table_args__ = (
        Index("ix_duels_code", "code"),
        Index("ix_duels_winner_id", "winner_id"),
        UniqueConstraint("event_id", "sequence_number")
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    duel_type_id = Column(Integer, ForeignKey("duel_types.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Properties
    sequence_number = Column(Integer, nullable=False)
    video_url = Column(String, nullable=True)

    # Relationships
    event = relationship("Event", foreign_keys=[event_id])
    duel_type = relationship("DuelType", foreign_keys=[duel_type_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    duel_participants = relationship(
        "DuelParticipant",
        back_populates="duel",
        cascade="all, delete-orphan"
    )
