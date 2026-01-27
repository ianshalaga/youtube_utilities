from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from services.ranking.storage.base import Base


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)

    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)
    order = Column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_rounds_battle_order", "battle_id", "order"),
        UniqueConstraint("battle_id", "order")
    )
