from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class DuelParticipant(Base):
    __tablename__ = "duel_participants"

    id = Column(Integer, primary_key=True)

    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
