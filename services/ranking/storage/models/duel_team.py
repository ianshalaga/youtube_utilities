from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class DuelTeam(Base):
    __tablename__ = "duel_teams"

    id = Column(Integer, primary_key=True)

    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
