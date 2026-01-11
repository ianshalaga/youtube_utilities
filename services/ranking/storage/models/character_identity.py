from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class CharacterIdentity(Base):
    __tablename__ = "character_identities"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    franchise = Column(String, nullable=False)
