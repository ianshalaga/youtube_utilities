from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
