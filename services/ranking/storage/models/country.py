from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Country(Base, WithCode):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)

    iso_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)

    __table_args__ = (
        Index("ix_countries_code", "code"),
    )
