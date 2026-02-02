from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Game(Base, WithCode):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    franchise_id = Column(
        Integer,
        ForeignKey("franchises.id"),
        nullable=False
    )

    franchise = relationship(
        "Franchise",
        back_populates="games"
    )

    __table_args__ = (
        Index("ix_game_code", "code"),
    )
