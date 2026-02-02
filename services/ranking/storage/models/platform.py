from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Platform(Base, WithCode):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)

    name = Column(String, unique=True, nullable=False)

    __table_args__ = (
        Index("ix_platforms_code", "code"),
    )
