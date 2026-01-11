from sqlalchemy import Column, Integer, String, ForeignKey
from services.ranking.storage.base import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    nickname = Column(String, unique=True, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
