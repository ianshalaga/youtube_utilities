from sqlalchemy import Column, Integer, ForeignKey
from services.ranking.storage.base import Base


class Battle(Base):
    __tablename__ = "battles"

    id = Column(Integer, primary_key=True)

    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)

    order = Column(Integer, nullable=False)
