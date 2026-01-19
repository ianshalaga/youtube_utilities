from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class DuelTeamMember(Base):
    __tablename__ = "duel_team_members"

    id = Column(Integer, primary_key=True)
    duel_team_id = Column(Integer, ForeignKey("duel_teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
