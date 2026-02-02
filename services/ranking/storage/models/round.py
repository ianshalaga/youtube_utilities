from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base


class Round(Base):
    __tablename__ = "rounds"

    __table_args__ = (
        Index("ix_rounds_battle_order", "battle_id", "order"),
        UniqueConstraint("battle_id", "order")
    )

    id = Column(Integer, primary_key=True)

    # Foreign Keys
    battle_id = Column(Integer, ForeignKey("battles.id"), nullable=False)

    # Attributes
    order = Column(Integer, nullable=False)

    # Relationships
    battle = relationship("Battle")
