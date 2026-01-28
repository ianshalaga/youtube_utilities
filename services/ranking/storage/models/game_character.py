from sqlalchemy import Column, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class GameCharacter(Base, WithCode):
    __tablename__ = "game_characters"

    __table_args__ = (
        Index("ix_game_characters_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    character_identity_id = Column(Integer, ForeignKey(
        "character_identities.id"), nullable=False)
    game_version_platform_id = Column(Integer, ForeignKey(
        "game_version_platforms.id"), nullable=False)

    # Relationships
    character_identity = relationship("CharacterIdentity")
    game_version_platform = relationship("GameVersionPlatform")
