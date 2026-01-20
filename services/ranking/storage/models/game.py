from sqlalchemy import Column, Integer, String, Index
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Game(Base, WithCode):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)

    name = Column(String, unique=True, nullable=False)

    __table_args__ = (
        Index("ix_games_code", "code"),
    )
