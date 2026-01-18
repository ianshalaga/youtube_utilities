from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from services.ranking.storage.base import Base


class GameVersion(Base):
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
