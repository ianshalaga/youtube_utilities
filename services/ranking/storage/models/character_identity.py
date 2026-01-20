from sqlalchemy import Column, Integer, String, Index
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class CharacterIdentity(Base, WithCode):
    __tablename__ = "character_identities"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)
    franchise = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_character_identities_code", "code"),
    )
