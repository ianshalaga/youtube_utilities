from sqlalchemy import Column, Integer, ForeignKey, String, Enum
from services.ranking.storage.base import Base


RoundResultCode = Enum(
    "W", "LB", "LY", "PW", "PL", "D", "0",
    name="round_result_code"
)


class RoundResult(Base):
    __tablename__ = "round_results"

    id = Column(Integer, primary_key=True)

    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    result_code = Column(RoundResultCode, nullable=False)
