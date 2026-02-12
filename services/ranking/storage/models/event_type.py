from sqlalchemy import Column, Integer, String, Index

from services.ranking.storage.base import Base


class EventType(Base):
    __tablename__ = "event_types"

    __table_args__ = (
        Index("ix_event_types_name", "name"),
    )

    id = Column(Integer, primary_key=True)

    # Fields
    name = Column(String, unique=True, nullable=False)
