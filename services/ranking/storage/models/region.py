from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
