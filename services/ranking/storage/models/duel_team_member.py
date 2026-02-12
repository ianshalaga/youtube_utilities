from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class DuelTeamMember(Base):
    __tablename__ = "duel_team_members"

    __table_args__ = (
        Index("ix_duel_team_members_player_id", "player_id"),
        Index("ix_duel_team_members_duel_team_id", "duel_team_id"),
        UniqueConstraint("duel_team_id", "player_id"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    duel_team_id = Column(Integer, ForeignKey("duel_teams.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    # Relationships
    duel_team = relationship("DuelTeam", back_populates="members")
    player = relationship("Player")
