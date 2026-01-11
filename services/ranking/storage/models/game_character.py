from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class GameCharacter(Base):
    __tablename__ = "game_characters"

    id = Column(Integer, primary_key=True)
    character_identity_id = Column(
        Integer, ForeignKey("character_identities.id"), nullable=False
    )
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    game_version_id = Column(Integer, ForeignKey(
        "game_versions.id"), nullable=False)
