from sqlalchemy import Column, Integer, String, ForeignKey, Index
from services.ranking.storage.base import Base
from services.ranking.storage.mixins import WithCode


class Player(Base, WithCode):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)

    country_id = Column(Integer, ForeignKey("countries.id"))

    nickname = Column(String, unique=True, nullable=False)

    __table_args__ = (
        Index("ix_players_code", "code"),
    )
