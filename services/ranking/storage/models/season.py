from sqlalchemy import Column, Integer, String, Date
from services.ranking.storage.base import Base


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)      # "2023", "Season 5", etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
