from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Team(Base, WithCode):
    __tablename__ = "teams"

    __table_args__ = (
        Index("ix_teams_code", "code"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, nullable=False)
