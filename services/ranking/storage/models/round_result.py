from sqlalchemy import Column, Integer, ForeignKey, Enum, UniqueConstraint, Index, String
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class RoundResult(Base):
    __tablename__ = "round_results"

    __table_args__ = (
        Index("ix_round_results_round_id", "round_id"),
        Index("ix_round_results_player_id", "player_id"),
        Index("ix_round_results_player_round", "player_id", "round_id"),
        UniqueConstraint("round_id", "player_id", name="uq_round_result"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    round_id = Column(
        Integer,
        ForeignKey("rounds.id", ondelete="CASCADE"),
        nullable=False
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Attributes
    result_code = Column(String(5), nullable=False)

    # Relationships
    round = relationship("Round", back_populates="round_results")
    player = relationship("Player")
