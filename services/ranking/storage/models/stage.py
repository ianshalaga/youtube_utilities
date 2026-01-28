from sqlalchemy import Column, Integer, String, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Stage(Base, WithCode):
    __tablename__ = "stages"

    __table_args__ = (
        Index("ix_stages_game_version_platform_id", "game_version_platform_id"),
        Index("ix_stages_name", "name"),
        UniqueConstraint(
            "name",
            "game_version_platform_id",
            name="uq_stage_name_game_version_platform"
        ),
    )

    id = Column(Integer, primary_key=True)

    # Forein Key
    game_version_platform_id = Column(
        Integer,
        ForeignKey("game_version_platforms.id"),
        nullable=False,
    )

    # Attributes
    name = Column(String, nullable=False)

    # Relationships
    game_version_platform = relationship("GameVersionPlatform")
