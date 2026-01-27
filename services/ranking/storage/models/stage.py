from sqlalchemy import Column, Integer, String, ForeignKey, Index
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Stage(Base, WithCode):
    __tablename__ = "stages"

    __table_args__ = (
        Index("ix_stages_game_version_platform_id", "game_version_platform_id"),
        Index("ix_stages_name", "name"),
    )

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    game_version_platform_id = Column(
        Integer,
        ForeignKey("game_version_platforms.id"),
        nullable=False,
    )
