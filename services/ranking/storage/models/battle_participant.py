from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class BattleParticipant(Base):
    __tablename__ = "battle_participants"

    id = Column(Integer, primary_key=True)
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    game_character_id = Column(Integer, ForeignKey(
        "game_characters.id"), nullable=False)
