from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from services.ranking.storage.base import Base


class DuelParticipant(Base):
    __tablename__ = "duel_participants"

    id = Column(Integer, primary_key=True)

    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    __table_args__ = (
        Index("ix_duel_participants_player_id", "player_id"),
        Index("ix_duel_participants_duel_id", "duel_id"),
        UniqueConstraint(
            "duel_id",
            "player_id",
            name="uq_duel_participant"
        ),
    )
