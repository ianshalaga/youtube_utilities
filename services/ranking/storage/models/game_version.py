from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class GameVersion(Base, WithCode):
    __tablename__ = "game_versions"

    id = Column(Integer, primary_key=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)

    version = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "platform_id",
            "version",
            name="uq_game_platform_version"
        ),
    )

    __table_args__ = (
        Index("ix_game_versions_code", "code"),
    )
