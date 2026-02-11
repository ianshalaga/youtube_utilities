from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class BattleParticipant(Base):
    __tablename__ = "battle_participants"

    __table_args__ = (
        Index("ix_battle_participants_battle_id", "battle_id"),
        Index("ix_battle_participants_player_id", "player_id"),
        UniqueConstraint(
            "battle_id",
            "player_id",
            name="uq_battle_player"
        ),
        UniqueConstraint(
            "battle_id",
            "position",
            name="uq_battle_position"
        ),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_character_id = Column(
        Integer, ForeignKey("game_characters.id"), nullable=False
    )
    duel_team_id = Column(
        Integer, ForeignKey("duel_teams.id"), nullable=True
    )

    position = Column(Integer, nullable=False)

    # Relationships
    player = relationship("Player", foreign_keys=[player_id])
    game_character = relationship(
        "GameCharacter", foreign_keys=[game_character_id])
    duel_team = relationship("DuelTeam", foreign_keys=[duel_team_id])
    battle = relationship(
        "Battle",
        back_populates="battle_participants",
        foreign_keys=[battle_id],
    )
