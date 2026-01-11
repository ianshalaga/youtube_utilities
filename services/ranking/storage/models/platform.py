from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
