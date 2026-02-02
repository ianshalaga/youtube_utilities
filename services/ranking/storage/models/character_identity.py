from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class CharacterIdentity(Base, WithCode):
    __tablename__ = "character_identities"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)

    franchise_id = Column(
        Integer,
        ForeignKey("franchises.id"),
        nullable=False
    )

    franchise = relationship(
        "Franchise",
        back_populates="character_identities"
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            "franchise_id",
            name="uq_character_identity"
        ),
    )

    # Relationships
    game_characters = relationship(
        "GameCharacter",
        back_populates="character_identity"
    )
