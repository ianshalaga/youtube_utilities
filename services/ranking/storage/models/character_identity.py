from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class CharacterIdentity(Base, WithCode):
    __tablename__ = "character_identities"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "franchise_id",
            name="uq_character_identity"
        ),
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    franchise_id = Column(
        Integer,
        ForeignKey("franchises.id", ondelete="RESTRICT"),
        nullable=False
    )

    # Fields
    name = Column(String, nullable=False)

    # Relationships
    franchise = relationship(
        "Franchise", back_populates="character_identities")

    game_characters = relationship(
        "GameCharacter", back_populates="character_identity")
