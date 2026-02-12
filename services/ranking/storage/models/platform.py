from sqlalchemy import Column, Integer, String, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Platform(Base, WithCode):
    __tablename__ = "platforms"

    __table_args__ = (
        Index("ix_platforms_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, unique=True, nullable=False)

    # Relationships
    game_versions = relationship(
        "GameVersionPlatform",
        back_populates="platform",
        cascade="all, delete-orphan"
    )
