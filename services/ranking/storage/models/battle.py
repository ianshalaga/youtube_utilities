from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from services.ranking.storage.base import Base


class Battle(Base):
    __tablename__ = "battles"

    __table_args__ = (
        Index("ix_battles_duel_order", "duel_id", "order"),
        Index("ix_battles_stage_id", "stage_id"),
        UniqueConstraint("duel_id", "order")
    )

    id = Column(Integer, primary_key=True)

    # Foreign keys
    duel_id = Column(Integer, ForeignKey("duels.id"), nullable=False)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False)

    # Properties
    order = Column(Integer, nullable=False)

    # Relationships
    duel = relationship("Duel")
    stage = relationship("Stage")
