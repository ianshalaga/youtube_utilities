from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class DuelTeam(Base):
    __tablename__ = "duel_teams"

    __table_args__ = (
        UniqueConstraint("duel_id", "team_id"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Relationships
    duel = relationship("Duel")
    team = relationship("Team")
