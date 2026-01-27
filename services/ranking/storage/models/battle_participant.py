from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Index
from services.ranking.storage.base import Base


class BattleParticipant(Base):
    __tablename__ = "battle_participants"

    id = Column(Integer, primary_key=True)

    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_character_id = Column(Integer, ForeignKey(
        "game_characters.id"), nullable=False)
    duel_team_id = Column(Integer, ForeignKey("duel_teams.id"), nullable=True)

    __table_args__ = (
        Index("ix_battle_participants_battle_id", "battle_id"),
        Index("ix_battle_participants_player_id", "player_id"),
        UniqueConstraint(
            "battle_id",
            "player_id",
            name="uq_battle_player"
        )
    )
