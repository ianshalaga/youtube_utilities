from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class DuelType(Base):
    __tablename__ = "duel_types"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
