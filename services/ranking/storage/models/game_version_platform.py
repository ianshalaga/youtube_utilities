from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class GameVersionPlatform(Base, WithCode):
    __tablename__ = "game_version_platforms"

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "platform_id",
            "version",
            name="uq_game_platform_version"
        ),
        Index("ix_game_versions_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    # Fields
    version = Column(String, nullable=False)

    # Relationships
    game = relationship("Game")
    platform = relationship("Platform")
