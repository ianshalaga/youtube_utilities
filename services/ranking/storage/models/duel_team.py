from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class DuelTeam(Base):
    __tablename__ = "duel_teams"

    __table_args__ = (
        Index("ix_duel_teams_duel_id", "duel_id"),
        Index("ix_duel_teams_team_id", "team_id"),
        UniqueConstraint("duel_id", "team_id", name="uq_duel_team")
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)

    # Relationships
    duel = relationship("Duel", back_populates="duel_teams")
    team = relationship("Team")

    members = relationship(
        "DuelTeamMember",
        back_populates="duel_team",
        cascade="all, delete-orphan"
    )
