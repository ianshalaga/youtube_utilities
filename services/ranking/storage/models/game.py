from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Game(Base, WithCode):
    __tablename__ = "games"

    __table_args__ = (
        Index("ix_game_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    franchise_id = Column(
        Integer,
        ForeignKey("franchises.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Fields
    name = Column(String, nullable=False)

    # Relationships
    franchise = relationship("Franchise", back_populates="games")

    game_versions = relationship(
        "GameVersionPlatform",
        back_populates="game",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
