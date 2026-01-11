from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class Duel(Base):
    __tablename__ = "duels"

    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey(
        "tournaments.id"), nullable=False)
    order = Column(Integer, nullable=False)
