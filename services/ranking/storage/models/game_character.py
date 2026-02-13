from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class GameCharacter(Base, WithCode):
    __tablename__ = "game_characters"

    __table_args__ = (
        Index("ix_game_characters_code", "code"),
        UniqueConstraint(
            "character_identity_id",
            "game_version_platform_id",
            name="uq_game_character_character_identity_game_version_platform"
        )
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    character_identity_id = Column(
        Integer,
        ForeignKey("character_identities.id", ondelete="CASCADE"),
        nullable=False
    )

    game_version_platform_id = Column(
        Integer,
        ForeignKey("game_version_platforms.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Relationships
    character_identity = relationship(
        "CharacterIdentity",
        back_populates="game_characters"
    )

    game_version_platform = relationship(
        "GameVersionPlatform",
        back_populates="game_characters"
    )
