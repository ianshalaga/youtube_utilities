from sqlalchemy import Column, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


RoundResultCode = Enum(
    "W", "LB", "LY", "PW", "PL", "D",
    name="round_result_code"
)


class RoundResult(Base):
    __tablename__ = "round_results"

    __table_args__ = (
        UniqueConstraint("round_id", "player_id", name="uq_round_player")
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Attributes
    result_code = Column(RoundResultCode, nullable=False)

    # Relationships
    round = relationship("Round", back_populates="round_results")
    player = relationship("Player")
