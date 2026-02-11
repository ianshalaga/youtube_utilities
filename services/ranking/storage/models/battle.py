from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class Battle(Base):
    __tablename__ = "battles"

    __table_args__ = (
        Index("ix_battles_duel_sequence", "duel_id", "sequence_number"),
        Index("ix_battles_stage_id", "stage_id"),
        UniqueConstraint("duel_id", "sequence_number"),
        CheckConstraint(
            """
            (is_draw = TRUE AND winner_id IS NULL AND loser_id IS NULL)
            OR
            (is_draw = FALSE AND winner_id IS NOT NULL AND loser_id IS NOT NULL)
            """,
            name="ck_battle_draw_consistency"
        ),
        CheckConstraint(
            "winner_id IS NULL OR loser_id IS NULL OR winner_id <> loser_id",
            name="ck_battle_winner_not_equal_loser"
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    loser_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    # Properties
    is_draw = Column(Boolean, nullable=False, default=False)
    sequence_number = Column(Integer, nullable=False)

    # Relationships
    duel = relationship("Duel", foreign_keys=[duel_id])
    stage = relationship("Stage", foreign_keys=[stage_id])
    winner = relationship("Player", foreign_keys=[winner_id])
    loser = relationship("Player", foreign_keys=[loser_id])
    battle_participants = relationship(
        "BattleParticipant",
        back_populates="battle",
        cascade="all, delete-orphan",
    )
