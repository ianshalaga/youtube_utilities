from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class DuelParticipant(Base):
    __tablename__ = "duel_participants"

    __table_args__ = (
        Index("ix_duel_participants_player_id", "player_id"),
        Index("ix_duel_participants_duel_id", "duel_id"),
        UniqueConstraint(
            "duel_id",
            "player_id",
            name="uq_duel_participant"
        ),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    duel_id = Column(
        Integer,
        ForeignKey("duels.id", ondelete="CASCADE"),
        nullable=False
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Relationships
    duel = relationship("Duel", back_populates="duel_participants")
    player = relationship("Player")
