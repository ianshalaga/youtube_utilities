from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class Battle(Base):
    __tablename__ = "battles"

    __table_args__ = (
        Index("ix_battles_duel_sequence", "duel_id", "sequence_number"),
        Index("ix_battles_stage_id", "stage_id"),
        Index("ix_battles_winner_id", "winner_id"),
        Index("ix_battles_loser_id", "loser_id"),
        UniqueConstraint("duel_id", "sequence_number",
                         name="uq_battle_duel_sequence"),
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
    duel_id = Column(
        Integer,
        ForeignKey("duels.id", ondelete="CASCADE"),
        nullable=False
    )

    stage_id = Column(
        Integer,
        ForeignKey("stages.id", ondelete="RESTRICT"),
        nullable=False
    )

    winner_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=True
    )

    loser_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=True
    )

    # Fields
    is_draw = Column(Boolean, nullable=False, default=False)
    sequence_number = Column(Integer, nullable=False)

    # Relationships
    duel = relationship("Duel", back_populates="battles")
    stage = relationship("Stage")
    winner = relationship("Player", foreign_keys=[winner_id])
    loser = relationship("Player", foreign_keys=[loser_id])

    battle_participants = relationship(
        "BattleParticipant",
        back_populates="battle",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    rounds = relationship(
        "Round",
        back_populates="battle",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
