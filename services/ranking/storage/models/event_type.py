from sqlalchemy import Column, Integer, String
from services.ranking.storage.base import Base


class EventType(Base):
    __tablename__ = "event_types"

    id = Column(Integer, primary_key=True)

    name = Column(String, unique=True, nullable=False)
