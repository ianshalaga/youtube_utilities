from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint, Boolean, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class Round(Base):
    __tablename__ = "rounds"

    __table_args__ = (
        Index("ix_rounds_battle_sequence", "battle_id", "sequence_number"),
        UniqueConstraint("battle_id", "sequence_number"),
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
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    loser_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    # Fields
    is_draw = Column(Boolean, nullable=False, default=False)
    sequence_number = Column(Integer, nullable=False)

    # Relationships
    battle = relationship("Battle", back_populates="rounds")
    winner = relationship("Player")
    loser = relationship("Player")

    round_results = relationship(
        "RoundResult",
        back_populates="round",
        cascade="all, delete-orphan"
    )
