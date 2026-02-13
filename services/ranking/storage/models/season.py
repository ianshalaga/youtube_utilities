from sqlalchemy import Column, Integer, String, Date, Index, CheckConstraint
from sqlalchemy.orm import relationship

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Season(Base, WithCode):
    __tablename__ = "seasons"

    __table_args__ = (
        Index("ix_seasons_code", "code"),
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_season_date_consistency"
        )
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    # Relationships
    events = relationship(
        "Event",
        back_populates="season",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
