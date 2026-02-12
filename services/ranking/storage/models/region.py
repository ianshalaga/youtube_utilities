from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Region(Base, WithCode):
    __tablename__ = "regions"

    __table_args__ = (
        Index("ix_regions_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, unique=True, nullable=False)
