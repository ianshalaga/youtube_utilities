from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)

    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)

    order = Column(Integer, nullable=False)
