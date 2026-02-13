from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class Round(Base):
    __tablename__ = "rounds"

    __table_args__ = (
        Index("ix_rounds_battle_sequence", "battle_id", "sequence_number"),
        Index("ix_rounds_battle_winner", "battle_id", "winner_id"),
        Index("ix_rounds_battle_loser", "battle_id", "loser_id"),
        UniqueConstraint(
            "battle_id",
            "sequence_number",
            name="uq_round_battle_sequence"
        ),
        CheckConstraint(
            """
            (is_draw = TRUE AND winner_id IS NULL AND loser_id IS NULL)
            OR
            (is_draw = FALSE AND winner_id IS NOT NULL AND loser_id IS NOT NULL)
            """,
            name="ck_round_draw_consistency"
        ),
        CheckConstraint(
            "winner_id IS NULL OR loser_id IS NULL OR winner_id <> loser_id",
            name="ck_round_winner_not_equal_loser"
        ),
        CheckConstraint(
            "sequence_number >= 1",
            name="ck_round_sequence_positive"
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    battle_id = Column(
        Integer,
        ForeignKey("battles.id", ondelete="CASCADE"),
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
    battle = relationship("Battle", back_populates="rounds")
    winner = relationship("Player", foreign_keys=[winner_id])
    loser = relationship("Player", foreign_keys=[loser_id])

    round_results = relationship(
        "RoundResult",
        back_populates="round",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
