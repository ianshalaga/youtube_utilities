from sqlalchemy import Column, Integer, String, Date, Index

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Season(Base, WithCode):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)

    name = Column(String, nullable=False)  # "2023", "Season 5", etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)

    __table_args__ = (
        Index("ix_seasons_code", "code"),
    )
