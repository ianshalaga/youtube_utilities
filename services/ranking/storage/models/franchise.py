from sqlalchemy import Column, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Franchise(Base, WithCode):
    __tablename__ = "franchises"

    __table_args__ = (
        UniqueConstraint("name", name="uq_franchise_name"),
        Index("ix_franchise_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    # Relationships
    character_identities = relationship(
        "CharacterIdentity",
        back_populates="franchise"
    )
    games = relationship(
        "Game",
        back_populates="franchise"
    )
