from sqlalchemy import Column, Integer, ForeignKey, String
from services.ranking.storage.base import Base


class RoundResult(Base):
    __tablename__ = "round_results"

    id = Column(Integer, primary_key=True)

    round_id = Column(Integer, ForeignKey("rounds.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    result_code = Column(String, nullable=False)  # W, LB, LY, PW, PL, D, 0
